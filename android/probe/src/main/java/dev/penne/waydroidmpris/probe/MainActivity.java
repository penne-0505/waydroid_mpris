package dev.penne.waydroidmpris.probe;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.provider.Settings;
import android.text.method.ScrollingMovementMethod;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import org.json.JSONObject;

public final class MainActivity extends Activity {
    private TextView statusView;
    private TextView outputView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        int pad = dp(16);
        root.setPadding(pad, pad, pad, pad);

        statusView = new TextView(this);
        statusView.setTextSize(16);
        root.addView(statusView);

        Button openSettings = new Button(this);
        openSettings.setText("Open notification listener settings");
        openSettings.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                startActivity(new Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS));
            }
        });
        root.addView(openSettings);

        Button launchAppleMusic = new Button(this);
        launchAppleMusic.setText("Launch Apple Music");
        launchAppleMusic.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                Intent launch = getPackageManager().getLaunchIntentForPackage(ProbeRunner.APPLE_MUSIC_PACKAGE);
                if (launch != null) {
                    startActivity(launch);
                }
            }
        });
        root.addView(launchAppleMusic);

        Button runProbe = new Button(this);
        runProbe.setText("Run media session probe");
        runProbe.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                runProbeAndRender();
            }
        });
        root.addView(runProbe);

        outputView = new TextView(this);
        outputView.setTextIsSelectable(true);
        outputView.setMovementMethod(new ScrollingMovementMethod());
        outputView.setTextSize(12);

        ScrollView scrollView = new ScrollView(this);
        scrollView.addView(outputView);
        root.addView(scrollView, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                0,
                1.0f));

        setContentView(root);
        runProbeAndRender();
    }

    @Override
    protected void onResume() {
        super.onResume();
        runProbeAndRender();
    }

    private void runProbeAndRender() {
        boolean enabled = ProbeRunner.isNotificationListenerEnabled(this);
        statusView.setText("Notification listener enabled: " + enabled);
        try {
            JSONObject probe = ProbeRunner.runProbe(this, "activity");
            outputView.setText(probe.toString(2));
        } catch (Exception ex) {
            outputView.setText(ProbeRunner.describeException(ex));
        }
    }

    private int dp(int value) {
        return (int) (value * getResources().getDisplayMetrics().density + 0.5f);
    }
}
