package com.foundfilmfriend.tv;

import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.app.Activity;
import android.graphics.Typeface;
import android.os.Bundle;
import android.util.Log;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.View;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.TextView;
import android.widget.Toast;

public class MainActivity extends Activity {

    private static final String APP_URL = "https://mr-akula.github.io/Found-Film-Friend/";
    private WebView webView;
    private final TVBridge tvBridge = new TVBridge();

    /** JS → Java bridge: страница сообщает нам какой экран активен */
    class TVBridge {
        volatile boolean browseActive = false;
        volatile boolean movieLoaded  = false;

        @JavascriptInterface
        public void onScreenChanged(String screen, boolean hasMovie) {
            browseActive = "browse".equals(screen);
            movieLoaded  = hasMovie;
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

        /* Root layout: WebView + native splash overlay */
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(0xFF0a0a0f);

        webView = new WebView(this);
        webView.setBackgroundColor(0xFF0a0a0f);
        root.addView(webView, new FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT,
            FrameLayout.LayoutParams.MATCH_PARENT));

        /* Splash shown while page loads */
        TextView splash = new TextView(this);
        splash.setText("🎬  Found Film Friend");
        splash.setTextColor(0xFFf0f0f8);
        splash.setTextSize(24);
        splash.setTypeface(null, Typeface.BOLD);
        splash.setGravity(Gravity.CENTER);
        splash.setBackgroundColor(0xFF0a0a0f);
        root.addView(splash, new FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT,
            FrameLayout.LayoutParams.MATCH_PARENT));

        setContentView(root);

        WebSettings s = webView.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setLoadWithOverviewMode(true);
        s.setUseWideViewPort(true);
        s.setCacheMode(WebSettings.LOAD_DEFAULT);
        s.setUserAgentString(s.getUserAgentString() + " FFF-AndroidTV/1.0");

        webView.addJavascriptInterface(tvBridge, "TVBridge");
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageFinished(WebView view, String url) {
                splash.animate()
                    .alpha(0f)
                    .setDuration(500)
                    .setListener(new AnimatorListenerAdapter() {
                        @Override public void onAnimationEnd(Animator a) {
                            splash.setVisibility(View.GONE);
                        }
                    });
            }
        });
        webView.setWebChromeClient(new WebChromeClient());

        webView.setOnKeyListener((v, keyCode, event) -> {
            if (event.getAction() != KeyEvent.ACTION_DOWN) return false;

            Log.d("FFF_TV", "Key received: " + keyCode + " browseActive=" + tvBridge.browseActive + " movieLoaded=" + tvBridge.movieLoaded);

            // На экране входа / других — не перехватываем, WebView сам управляет фокусом
            if (!tvBridge.browseActive) return false;

            // На экране просмотра фильма — D-pad = оценить фильм
            if (tvBridge.movieLoaded) {
                String jsKey = null;
                switch (keyCode) {
                    case KeyEvent.KEYCODE_DPAD_RIGHT: jsKey = "ArrowRight"; break;
                    case KeyEvent.KEYCODE_DPAD_LEFT:  jsKey = "ArrowLeft";  break;
                    case KeyEvent.KEYCODE_DPAD_UP:    jsKey = "ArrowUp";    break;
                }
                if (jsKey != null) {
                    final String key = jsKey;
                    Log.d("FFF_TV", "Dispatching JS key: " + key);
                    Toast.makeText(this, key, Toast.LENGTH_SHORT).show();
                    webView.post(() ->
                        webView.evaluateJavascript(
                            "document.dispatchEvent(new KeyboardEvent('keydown',{key:'" + key + "',bubbles:true}));",
                            null
                        )
                    );
                    return true;
                }
            }

            // OK/Enter на кнопках — кликаем активный элемент
            if (keyCode == KeyEvent.KEYCODE_DPAD_CENTER || keyCode == KeyEvent.KEYCODE_ENTER) {
                webView.post(() ->
                    webView.evaluateJavascript(
                        "(function(){var el=document.activeElement;" +
                        "if(el&&el.tagName==='BUTTON')el.click();})()",
                        null
                    )
                );
            }

            return false; // остальное WebView обрабатывает сам
        });

        webView.loadUrl(APP_URL);
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
    @Override protected void onDestroy() { webView.destroy(); super.onDestroy(); }
}
