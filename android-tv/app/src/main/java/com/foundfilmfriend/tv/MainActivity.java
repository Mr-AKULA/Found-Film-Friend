package com.foundfilmfriend.tv;

import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.app.Activity;
import android.graphics.Typeface;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.View;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.TextView;

public class MainActivity extends Activity {

    private static final String APP_URL = "https://mr-akula.github.io/Found-Film-Friend/";
    private static final String TAG     = "FFF_TV";

    private WebView  webView;
    private TextView splash;
    private boolean  splashDismissed = false;
    private volatile boolean inExternalPage = false;
    private final Handler  handler  = new Handler(Looper.getMainLooper());
    private final TVBridge tvBridge = new TVBridge();

    class TVBridge {
        @JavascriptInterface
        public void onScreenChanged(String screen, boolean hasMovie) {
            /* kept for compatibility — no longer used for key routing */
        }

        @JavascriptInterface
        public void openUrl(String url) {
            /* Load streaming page inside our WebView — no external browser needed */
            runOnUiThread(() -> {
                inExternalPage = true;
                webView.loadUrl(url);
            });
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        getWindow().getDecorView().setSystemUiVisibility(
            View.SYSTEM_UI_FLAG_LAYOUT_STABLE |
            View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION |
            View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN |
            View.SYSTEM_UI_FLAG_HIDE_NAVIGATION |
            View.SYSTEM_UI_FLAG_FULLSCREEN |
            View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
        );

        /* ── Root: WebView + splash overlay ── */
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(0xFF0a0a0f);

        webView = new WebView(this);
        webView.setBackgroundColor(0xFF0a0a0f);
        root.addView(webView, new FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT,
            FrameLayout.LayoutParams.MATCH_PARENT));

        splash = new TextView(this);
        splash.setText("Found Film Friend");
        splash.setTextColor(0xFFa78bfa);
        splash.setTextSize(28);
        splash.setTypeface(null, Typeface.BOLD);
        splash.setGravity(Gravity.CENTER);
        splash.setBackgroundColor(0xFF0a0a0f);
        root.addView(splash, new FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT,
            FrameLayout.LayoutParams.MATCH_PARENT));

        setContentView(root);

        /* ── WebView settings ── */
        WebSettings s = webView.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setLoadWithOverviewMode(true);
        s.setUseWideViewPort(true);
        s.setCacheMode(WebSettings.LOAD_DEFAULT);
        s.setUserAgentString(s.getUserAgentString() + " FFF-AndroidTV/1.0");

        webView.addJavascriptInterface(tvBridge, "TVBridge");
        webView.setWebChromeClient(new WebChromeClient());
        webView.setWebViewClient(new WebViewClient() {

            @Override
            public void onPageFinished(WebView view, String url) {
                Log.d(TAG, "onPageFinished: " + url);
                /* Back on our app — restore D-pad interception */
                if (url != null && url.startsWith("https://mr-akula.github.io")) {
                    inExternalPage = false;
                }
                dismissSplash();
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                /* Let WebView handle all URLs — streaming pages load inside WebView */
                return false;
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest req, android.webkit.WebResourceError err) {
                if (req.isForMainFrame() && !inExternalPage) {
                    Log.e(TAG, "Page error — retrying in 4s");
                    dismissSplash();
                    handler.postDelayed(() -> webView.reload(), 4000);
                }
            }
        });

        /* Fallback: hide splash after 15s no matter what */
        handler.postDelayed(this::dismissSplash, 15000);

        webView.setOnKeyListener((v, keyCode, event) -> {
            if (event.getAction() != KeyEvent.ACTION_DOWN) return false;

            /* On streaming page — pass D-pad through so player can use it */
            if (inExternalPage) return false;

            String jsKey = null;
            switch (keyCode) {
                case KeyEvent.KEYCODE_DPAD_RIGHT:  jsKey = "ArrowRight"; break;
                case KeyEvent.KEYCODE_DPAD_LEFT:   jsKey = "ArrowLeft";  break;
                case KeyEvent.KEYCODE_DPAD_UP:     jsKey = "ArrowUp";    break;
                case KeyEvent.KEYCODE_DPAD_DOWN:   jsKey = "ArrowDown";  break;
                case KeyEvent.KEYCODE_DPAD_CENTER:
                case KeyEvent.KEYCODE_ENTER:       jsKey = "Enter";      break;
            }
            if (jsKey == null) return false;

            final String key = jsKey;
            webView.post(() -> webView.evaluateJavascript(
                "document.dispatchEvent(new KeyboardEvent('keydown',{key:'" + key + "',bubbles:true,cancelable:true}));", null));
            return true;
        });

        webView.loadUrl(APP_URL);
    }

    private void dismissSplash() {
        if (splashDismissed || splash == null) return;
        splashDismissed = true;
        splash.animate().alpha(0f).setDuration(400).setListener(new AnimatorListenerAdapter() {
            @Override public void onAnimationEnd(Animator a) { splash.setVisibility(View.GONE); }
        });
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK && webView.canGoBack()) {
            webView.goBack();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

    @Override protected void onPause()   { super.onPause();   webView.onPause(); }
    @Override protected void onResume()  { super.onResume();  webView.onResume(); }
    @Override protected void onDestroy() {
        handler.removeCallbacksAndMessages(null);
        webView.destroy();
        super.onDestroy();
    }
}
