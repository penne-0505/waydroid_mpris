package dev.penne.waydroidmpris.probe;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;
import org.json.JSONObject;

public final class BridgeCommandReceiver extends BroadcastReceiver {
    public static final String ACTION_COMMAND = "dev.penne.waydroidmpris.probe.COMMAND";
    public static final String EXTRA_COMMAND = "command";
    public static final String EXTRA_POSITION_MS = "positionMs";

    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent == null || !ACTION_COMMAND.equals(intent.getAction())) {
            return;
        }
        String command = intent.getStringExtra(EXTRA_COMMAND);
        long positionMs = intent.getLongExtra(EXTRA_POSITION_MS, -1L);
        try {
            JSONObject result = ProbeRunner.dispatchCommand(context, command, positionMs);
            Log.i(ProbeRunner.TAG, "COMMAND_RESULT:" + result.toString());
        } catch (Exception ex) {
            Log.w(ProbeRunner.TAG, ProbeRunner.describeException(ex));
        }
    }
}
