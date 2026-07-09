package dev.penne.waydroidmpris.probe;

import android.content.ComponentName;
import android.content.Context;
import android.graphics.Bitmap;
import android.media.MediaDescription;
import android.media.MediaMetadata;
import android.media.session.MediaController;
import android.media.session.MediaSessionManager;
import android.media.session.PlaybackState;
import android.os.SystemClock;
import android.provider.Settings;
import android.text.TextUtils;
import android.util.Log;
import java.io.File;
import java.io.FileOutputStream;
import java.io.FileWriter;
import java.io.IOException;
import java.util.List;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

public final class ProbeRunner {
    public static final String APPLE_MUSIC_PACKAGE = "com.apple.android.music";
    public static final String TAG = "WaydroidMprisProbe";

    private ProbeRunner() {
    }

    public static JSONObject runProbe(Context context, String reason) throws JSONException, IOException {
        JSONObject root = new JSONObject();
        root.put("schema", "dev.penne.waydroid_mpris.probe.v0");
        root.put("reason", reason);
        root.put("targetPackage", APPLE_MUSIC_PACKAGE);
        root.put("notificationListenerEnabled", isNotificationListenerEnabled(context));

        MediaSessionManager manager = (MediaSessionManager) context.getSystemService(Context.MEDIA_SESSION_SERVICE);
        ComponentName listener = new ComponentName(context, ProbeNotificationListener.class);
        List<MediaController> controllers = manager.getActiveSessions(listener);

        JSONArray sessions = new JSONArray();
        JSONObject selected = null;
        for (MediaController controller : controllers) {
            JSONObject item = controllerToJson(context, controller);
            sessions.put(item);
            if (selected == null && APPLE_MUSIC_PACKAGE.equals(controller.getPackageName())) {
                selected = item;
            }
        }

        root.put("sessionCount", sessions.length());
        root.put("sessions", sessions);
        root.put("selectedAppleMusicSession", selected == null ? JSONObject.NULL : selected);
        writeProbeFiles(context, root);
        Log.i(TAG, "PROBE_JSON:" + root.toString());
        return root;
    }

    public static JSONObject dispatchCommand(Context context, String command, long positionMs) throws JSONException, IOException {
        JSONObject result = new JSONObject();
        result.put("schema", "dev.penne.waydroid_mpris.command_result.v0");
        result.put("command", command == null ? JSONObject.NULL : command);
        result.put("targetPackage", APPLE_MUSIC_PACKAGE);

        if (TextUtils.isEmpty(command)) {
            result.put("ok", false);
            result.put("error", "missing_command");
            writeCommandResult(context, result);
            return result;
        }

        MediaController controller = selectedAppleMusicController(context);
        if (controller == null) {
            result.put("ok", false);
            result.put("error", "apple_music_session_absent");
            writeCommandResult(context, result);
            runProbe(context, "command_failed_session_absent");
            return result;
        }

        MediaController.TransportControls controls = controller.getTransportControls();
        String normalized = normalizeCommand(command);
        boolean ok = true;
        String error = "";
        if ("play".equals(normalized)) {
            controls.play();
        } else if ("pause".equals(normalized)) {
            controls.pause();
        } else if ("playPause".equals(normalized)) {
            PlaybackState state = controller.getPlaybackState();
            if (state != null && state.getState() == PlaybackState.STATE_PLAYING) {
                controls.pause();
            } else {
                controls.play();
            }
        } else if ("next".equals(normalized)) {
            controls.skipToNext();
        } else if ("previous".equals(normalized)) {
            controls.skipToPrevious();
        } else if ("stop".equals(normalized)) {
            controls.stop();
        } else if ("seekTo".equals(normalized) && positionMs >= 0L) {
            controls.seekTo(positionMs);
        } else {
            ok = false;
            error = "unknown_or_incomplete_command";
        }

        result.put("ok", ok);
        if (!ok) {
            result.put("error", error);
        }
        result.put("normalizedCommand", normalized);
        result.put("packageName", controller.getPackageName());
        writeCommandResult(context, result);
        runProbe(context, ok ? "command_dispatched" : "command_rejected");
        return result;
    }

    public static void runProbeAndLog(Context context, String reason) {
        try {
            runProbe(context, reason);
        } catch (Exception ex) {
            Log.w(TAG, describeException(ex));
        }
    }

    public static boolean isNotificationListenerEnabled(Context context) {
        String enabledListeners = Settings.Secure.getString(
                context.getContentResolver(),
                "enabled_notification_listeners");
        if (TextUtils.isEmpty(enabledListeners)) {
            return false;
        }
        String packageName = context.getPackageName();
        String[] entries = enabledListeners.split(":");
        for (String entry : entries) {
            ComponentName component = ComponentName.unflattenFromString(entry);
            if (component != null && packageName.equals(component.getPackageName())) {
                return true;
            }
        }
        return false;
    }

    public static String describeException(Exception ex) {
        return ex.getClass().getName() + ": " + String.valueOf(ex.getMessage());
    }

    private static JSONObject controllerToJson(Context context, MediaController controller) throws JSONException, IOException {
        JSONObject item = new JSONObject();
        item.put("packageName", controller.getPackageName());
        item.put("metadata", metadataToJson(context, controller.getMetadata()));
        item.put("playbackState", playbackStateToJson(controller.getPlaybackState()));
        return item;
    }

    private static MediaController selectedAppleMusicController(Context context) {
        MediaSessionManager manager = (MediaSessionManager) context.getSystemService(Context.MEDIA_SESSION_SERVICE);
        ComponentName listener = new ComponentName(context, ProbeNotificationListener.class);
        List<MediaController> controllers = manager.getActiveSessions(listener);
        for (MediaController controller : controllers) {
            if (APPLE_MUSIC_PACKAGE.equals(controller.getPackageName())) {
                return controller;
            }
        }
        return null;
    }

    private static JSONObject metadataToJson(Context context, MediaMetadata metadata) throws JSONException, IOException {
        JSONObject out = new JSONObject();
        out.put("present", metadata != null);
        if (metadata == null) {
            return out;
        }

        putString(out, "mediaId", metadata.getString(MediaMetadata.METADATA_KEY_MEDIA_ID));
        putString(out, "title", metadata.getString(MediaMetadata.METADATA_KEY_TITLE));
        putString(out, "artist", metadata.getString(MediaMetadata.METADATA_KEY_ARTIST));
        putString(out, "album", metadata.getString(MediaMetadata.METADATA_KEY_ALBUM));
        putString(out, "albumArtist", metadata.getString(MediaMetadata.METADATA_KEY_ALBUM_ARTIST));
        putString(out, "displayTitle", metadata.getString(MediaMetadata.METADATA_KEY_DISPLAY_TITLE));
        putString(out, "displaySubtitle", metadata.getString(MediaMetadata.METADATA_KEY_DISPLAY_SUBTITLE));
        putString(out, "displayDescription", metadata.getString(MediaMetadata.METADATA_KEY_DISPLAY_DESCRIPTION));
        putString(out, "artUri", metadata.getString(MediaMetadata.METADATA_KEY_ART_URI));
        putString(out, "albumArtUri", metadata.getString(MediaMetadata.METADATA_KEY_ALBUM_ART_URI));
        putString(out, "displayIconUri", metadata.getString(MediaMetadata.METADATA_KEY_DISPLAY_ICON_URI));

        long duration = metadata.getLong(MediaMetadata.METADATA_KEY_DURATION);
        if (duration > 0) {
            out.put("durationMs", duration);
        }

        MediaDescription description = metadata.getDescription();
        if (description != null) {
            JSONObject desc = new JSONObject();
            putCharSequence(desc, "title", description.getTitle());
            putCharSequence(desc, "subtitle", description.getSubtitle());
            putCharSequence(desc, "description", description.getDescription());
            if (description.getIconUri() != null) {
                desc.put("iconUri", description.getIconUri().toString());
            }
            out.put("description", desc);
        }

        JSONObject artwork = new JSONObject();
        artwork.put("art", bitmapToJson(metadata.getBitmap(MediaMetadata.METADATA_KEY_ART)));
        artwork.put("albumArt", bitmapToJson(metadata.getBitmap(MediaMetadata.METADATA_KEY_ALBUM_ART)));
        artwork.put("displayIcon", bitmapToJson(metadata.getBitmap(MediaMetadata.METADATA_KEY_DISPLAY_ICON)));
        out.put("artwork", artwork);
        out.put("artworkFile", exportArtworkFile(context, metadata));
        return out;
    }

    private static JSONObject playbackStateToJson(PlaybackState state) throws JSONException {
        JSONObject out = new JSONObject();
        out.put("present", state != null);
        if (state == null) {
            return out;
        }
        long rawPositionMs = state.getPosition();
        float speed = state.getPlaybackSpeed();
        long updateTimeMs = state.getLastPositionUpdateTime();
        long nowMs = SystemClock.elapsedRealtime();
        long positionMs = projectedPositionMs(state.getState(), rawPositionMs, speed, updateTimeMs, nowMs);

        out.put("state", stateName(state.getState()));
        out.put("stateCode", state.getState());
        out.put("positionMs", positionMs);
        out.put("rawPositionMs", rawPositionMs);
        out.put("speed", speed);
        out.put("updateTimeMs", updateTimeMs);
        out.put("probeElapsedRealtimeMs", nowMs);
        long actions = state.getActions();
        out.put("actionsRaw", actions);
        out.put("actions", actionsToJson(actions));
        return out;
    }

    private static long projectedPositionMs(int state, long rawPositionMs, float speed, long updateTimeMs, long nowMs) {
        if (rawPositionMs < 0L) {
            return rawPositionMs;
        }
        if (state != PlaybackState.STATE_PLAYING || speed <= 0.0f || updateTimeMs <= 0L || nowMs < updateTimeMs) {
            return rawPositionMs;
        }
        return rawPositionMs + (long) ((nowMs - updateTimeMs) * speed);
    }

    private static JSONArray actionsToJson(long actions) {
        JSONArray out = new JSONArray();
        addAction(out, actions, PlaybackState.ACTION_PLAY, "play");
        addAction(out, actions, PlaybackState.ACTION_PAUSE, "pause");
        addAction(out, actions, PlaybackState.ACTION_PLAY_PAUSE, "playPause");
        addAction(out, actions, PlaybackState.ACTION_SKIP_TO_NEXT, "next");
        addAction(out, actions, PlaybackState.ACTION_SKIP_TO_PREVIOUS, "previous");
        addAction(out, actions, PlaybackState.ACTION_SEEK_TO, "seekTo");
        addAction(out, actions, PlaybackState.ACTION_STOP, "stop");
        addAction(out, actions, PlaybackState.ACTION_FAST_FORWARD, "fastForward");
        addAction(out, actions, PlaybackState.ACTION_REWIND, "rewind");
        return out;
    }

    private static void addAction(JSONArray out, long actions, long action, String name) {
        if ((actions & action) != 0L) {
            out.put(name);
        }
    }

    private static JSONObject bitmapToJson(Bitmap bitmap) throws JSONException {
        JSONObject out = new JSONObject();
        out.put("present", bitmap != null);
        if (bitmap != null) {
            out.put("width", bitmap.getWidth());
            out.put("height", bitmap.getHeight());
            out.put("byteCount", bitmap.getByteCount());
        }
        return out;
    }

    private static JSONObject exportArtworkFile(Context context, MediaMetadata metadata) throws JSONException, IOException {
        ArtworkSelection selection = selectArtwork(metadata);
        JSONObject out = new JSONObject();
        out.put("present", selection.bitmap != null);
        if (selection.bitmap == null) {
            return out;
        }

        File externalDir = context.getExternalFilesDir("artwork");
        if (externalDir == null) {
            out.put("present", false);
            out.put("error", "external_files_unavailable");
            return out;
        }
        if (!externalDir.exists() && !externalDir.mkdirs()) {
            out.put("present", false);
            out.put("error", "artwork_dir_create_failed");
            return out;
        }

        String nameSeed = metadata.getString(MediaMetadata.METADATA_KEY_MEDIA_ID);
        if (TextUtils.isEmpty(nameSeed)) {
            nameSeed = metadata.getString(MediaMetadata.METADATA_KEY_TITLE);
        }
        String safeName = sanitizeFileName(nameSeed);
        File file = new File(externalDir, safeName + ".png");
        File tmpFile = new File(externalDir, safeName + ".png.tmp");
        FileOutputStream stream = new FileOutputStream(tmpFile, false);
        try {
            if (!selection.bitmap.compress(Bitmap.CompressFormat.PNG, 100, stream)) {
                throw new IOException("Bitmap compression returned false");
            }
        } finally {
            stream.close();
        }
        if (file.exists() && !file.delete()) {
            throw new IOException("Failed to replace existing artwork file");
        }
        if (!tmpFile.renameTo(file)) {
            throw new IOException("Failed to publish artwork file");
        }

        out.put("source", selection.source);
        out.put("path", file.getAbsolutePath());
        out.put("mimeType", "image/png");
        out.put("width", selection.bitmap.getWidth());
        out.put("height", selection.bitmap.getHeight());
        out.put("byteCount", file.length());
        return out;
    }

    private static ArtworkSelection selectArtwork(MediaMetadata metadata) {
        Bitmap albumArt = metadata.getBitmap(MediaMetadata.METADATA_KEY_ALBUM_ART);
        if (albumArt != null) {
            return new ArtworkSelection("albumArt", albumArt);
        }
        Bitmap displayIcon = metadata.getBitmap(MediaMetadata.METADATA_KEY_DISPLAY_ICON);
        if (displayIcon != null) {
            return new ArtworkSelection("displayIcon", displayIcon);
        }
        Bitmap art = metadata.getBitmap(MediaMetadata.METADATA_KEY_ART);
        if (art != null) {
            return new ArtworkSelection("art", art);
        }
        return new ArtworkSelection("", null);
    }

    private static String sanitizeFileName(String raw) {
        String value = TextUtils.isEmpty(raw) ? "current" : raw;
        String safe = value.replaceAll("[^A-Za-z0-9._-]", "_");
        if (TextUtils.isEmpty(safe)) {
            return "current";
        }
        return safe.length() > 80 ? safe.substring(0, 80) : safe;
    }

    private static void putString(JSONObject object, String key, String value) throws JSONException {
        if (!TextUtils.isEmpty(value)) {
            object.put(key, value);
        }
    }

    private static void putCharSequence(JSONObject object, String key, CharSequence value) throws JSONException {
        if (!TextUtils.isEmpty(value)) {
            object.put(key, value.toString());
        }
    }

    private static String stateName(int state) {
        switch (state) {
            case PlaybackState.STATE_NONE:
                return "none";
            case PlaybackState.STATE_STOPPED:
                return "stopped";
            case PlaybackState.STATE_PAUSED:
                return "paused";
            case PlaybackState.STATE_PLAYING:
                return "playing";
            case PlaybackState.STATE_FAST_FORWARDING:
                return "fastForwarding";
            case PlaybackState.STATE_REWINDING:
                return "rewinding";
            case PlaybackState.STATE_BUFFERING:
                return "buffering";
            case PlaybackState.STATE_ERROR:
                return "error";
            case PlaybackState.STATE_CONNECTING:
                return "connecting";
            case PlaybackState.STATE_SKIPPING_TO_PREVIOUS:
                return "skippingToPrevious";
            case PlaybackState.STATE_SKIPPING_TO_NEXT:
                return "skippingToNext";
            case PlaybackState.STATE_SKIPPING_TO_QUEUE_ITEM:
                return "skippingToQueueItem";
            default:
                return "unknown";
        }
    }

    private static String normalizeCommand(String command) {
        if ("play-pause".equals(command) || "play_pause".equals(command) || "toggle".equals(command)) {
            return "playPause";
        }
        if ("next".equals(command) || "skipToNext".equals(command)) {
            return "next";
        }
        if ("previous".equals(command) || "skipToPrevious".equals(command)) {
            return "previous";
        }
        if ("seek".equals(command)) {
            return "seekTo";
        }
        return command;
    }

    private static void writeProbeFiles(Context context, JSONObject probe) throws IOException {
        writeFile(new File(context.getFilesDir(), "latest_probe.json"), probe);
        File externalDir = context.getExternalFilesDir(null);
        if (externalDir != null) {
            writeFile(new File(externalDir, "latest_probe.json"), probe);
        }
    }

    private static void writeCommandResult(Context context, JSONObject result) throws IOException {
        writeFile(new File(context.getFilesDir(), "latest_command_result.json"), result);
        File externalDir = context.getExternalFilesDir(null);
        if (externalDir != null) {
            writeFile(new File(externalDir, "latest_command_result.json"), result);
        }
    }

    private static void writeFile(File file, JSONObject probe) throws IOException {
        File parent = file.getParentFile();
        if (parent != null && !parent.exists() && !parent.mkdirs()) {
            throw new IOException("Failed to create " + parent);
        }
        FileWriter writer = new FileWriter(file, false);
        try {
            writer.write(probe.toString(2));
            writer.write('\n');
        } catch (JSONException ex) {
            throw new IOException(ex);
        } finally {
            writer.close();
        }
    }

    private static final class ArtworkSelection {
        final String source;
        final Bitmap bitmap;

        ArtworkSelection(String source, Bitmap bitmap) {
            this.source = source;
            this.bitmap = bitmap;
        }
    }
}
