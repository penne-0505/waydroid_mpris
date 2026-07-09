package dev.penne.waydroidmpris.probe;

import android.content.ComponentName;
import android.media.session.MediaController;
import android.media.session.MediaSessionManager;
import android.service.notification.NotificationListenerService;
import android.service.notification.StatusBarNotification;
import android.util.Log;
import java.util.ArrayList;
import java.util.List;

public final class ProbeNotificationListener extends NotificationListenerService {
    private final List<MediaController> registeredControllers = new ArrayList<>();
    private final MediaController.Callback mediaCallback = new MediaController.Callback() {
        @Override
        public void onMetadataChanged(android.media.MediaMetadata metadata) {
            ProbeRunner.runProbeAndLog(ProbeNotificationListener.this, "media_metadata_changed");
        }

        @Override
        public void onPlaybackStateChanged(android.media.session.PlaybackState state) {
            ProbeRunner.runProbeAndLog(ProbeNotificationListener.this, "media_playback_state_changed");
        }

        @Override
        public void onSessionDestroyed() {
            ProbeRunner.runProbeAndLog(ProbeNotificationListener.this, "media_session_destroyed");
            refreshAppleMusicCallbacks("media_session_destroyed");
        }
    };

    @Override
    public void onListenerConnected() {
        super.onListenerConnected();
        refreshAppleMusicCallbacks("listener_connected");
        ProbeRunner.runProbeAndLog(this, "listener_connected");
    }

    @Override
    public void onListenerDisconnected() {
        unregisterAppleMusicCallbacks();
        super.onListenerDisconnected();
    }

    @Override
    public void onNotificationPosted(StatusBarNotification sbn) {
        if (sbn != null && ProbeRunner.APPLE_MUSIC_PACKAGE.equals(sbn.getPackageName())) {
            refreshAppleMusicCallbacks("apple_music_notification_posted");
            ProbeRunner.runProbeAndLog(this, "apple_music_notification_posted");
        }
    }

    @Override
    public void onNotificationRemoved(StatusBarNotification sbn) {
        if (sbn != null && ProbeRunner.APPLE_MUSIC_PACKAGE.equals(sbn.getPackageName())) {
            refreshAppleMusicCallbacks("apple_music_notification_removed");
            ProbeRunner.runProbeAndLog(this, "apple_music_notification_removed");
        }
    }

    private void refreshAppleMusicCallbacks(String reason) {
        unregisterAppleMusicCallbacks();
        try {
            MediaSessionManager manager = (MediaSessionManager) getSystemService(MEDIA_SESSION_SERVICE);
            ComponentName listener = new ComponentName(this, ProbeNotificationListener.class);
            List<MediaController> controllers = manager.getActiveSessions(listener);
            for (MediaController controller : controllers) {
                if (ProbeRunner.APPLE_MUSIC_PACKAGE.equals(controller.getPackageName())) {
                    controller.registerCallback(mediaCallback);
                    registeredControllers.add(controller);
                }
            }
        } catch (Exception ex) {
            Log.w(ProbeRunner.TAG, "Failed to refresh callbacks after " + reason + ": " + ProbeRunner.describeException(ex));
        }
    }

    private void unregisterAppleMusicCallbacks() {
        for (MediaController controller : registeredControllers) {
            try {
                controller.unregisterCallback(mediaCallback);
            } catch (Exception ex) {
                Log.w(ProbeRunner.TAG, "Failed to unregister callback: " + ProbeRunner.describeException(ex));
            }
        }
        registeredControllers.clear();
    }
}
