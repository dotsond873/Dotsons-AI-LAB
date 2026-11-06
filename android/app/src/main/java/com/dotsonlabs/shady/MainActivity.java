package com.dotsonlabs.shady;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Insets;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.WindowInsets;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebChromeClient;
import android.webkit.ValueCallback;
import android.webkit.JavascriptInterface;
import android.print.PrintManager;
import android.print.PrintAttributes;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.window.OnBackInvokedDispatcher;

public class MainActivity extends Activity {
    private static final String HOST = "dotsons-ai-lab-frontend.onrender.com";
    private static final String HOME = "https://" + HOST + "/";
    private WebView webView;
    private ValueCallback<Uri[]> fileCallback;
    private static final int PICK_FILES = 101;
    private LinearLayout errorPanel;

    @Override
    public void onCreate(Bundle state) {
        super.onCreate(state);
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.rgb(8, 13, 16));
        root.setOnApplyWindowInsetsListener((view, windowInsets) -> {
            if (Build.VERSION.SDK_INT >= 30) {
                Insets insets = windowInsets.getInsets(
                    WindowInsets.Type.systemBars() | WindowInsets.Type.ime());
                view.setPadding(insets.left, insets.top, insets.right, insets.bottom);
            } else {
                view.setPadding(windowInsets.getSystemWindowInsetLeft(),
                    windowInsets.getSystemWindowInsetTop(),
                    windowInsets.getSystemWindowInsetRight(),
                    windowInsets.getSystemWindowInsetBottom());
            }
            return windowInsets;
        });
        webView = new WebView(this);
        webView.setBackgroundColor(Color.rgb(8, 13, 16));
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(true); // Needed for user-selected content:// document URIs.
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setUserAgentString(settings.getUserAgentString() + " ShadyAndroid/1.0");
        webView.addJavascriptInterface(new Object() {
            @JavascriptInterface
            public void printChat() {
                runOnUiThread(() -> {
                    Uri current = Uri.parse(webView.getUrl() == null ? "" : webView.getUrl());
                    if (!"https".equals(current.getScheme()) || !HOST.equals(current.getHost())) return;
                    PrintManager manager = (PrintManager) getSystemService(PRINT_SERVICE);
                    if (manager != null) manager.print("Shady chat", webView.createPrintDocumentAdapter("Shady chat"), new PrintAttributes.Builder().build());
                });
            }
        }, "ShadyAndroid");
        root.addView(webView, new FrameLayout.LayoutParams(-1, -1));

        errorPanel = new LinearLayout(this);
        errorPanel.setOrientation(LinearLayout.VERTICAL);
        errorPanel.setGravity(Gravity.CENTER);
        errorPanel.setPadding(32, 32, 32, 32);
        errorPanel.setBackgroundColor(Color.rgb(8, 13, 16));
        TextView message = new TextView(this);
        message.setText(R.string.connection_error);
        message.setTextColor(Color.rgb(176, 242, 233));
        message.setTextSize(18);
        message.setGravity(Gravity.CENTER);
        errorPanel.addView(message);
        Button retry = new Button(this);
        retry.setText(R.string.retry);
        retry.setOnClickListener(view -> {
            errorPanel.setVisibility(View.GONE);
            webView.loadUrl(HOME);
        });
        errorPanel.addView(retry);
        errorPanel.setVisibility(View.GONE);
        root.addView(errorPanel, new FrameLayout.LayoutParams(-1, -1));
        setContentView(root);
        root.requestApplyInsets();

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                if (!request.isForMainFrame()) return false;
                Uri uri = request.getUrl();
                if ("https".equals(uri.getScheme()) && HOST.equals(uri.getHost())
                        && !"/download.html".equals(uri.getPath())) return false;
                openBrowser(uri);
                return true;
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame()) errorPanel.setVisibility(View.VISIBLE);
            }

            @Override
            public void onReceivedHttpError(WebView view, WebResourceRequest request, WebResourceResponse response) {
                if (request.isForMainFrame()) errorPanel.setVisibility(View.VISIBLE);
            }
        });
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback,
                                             FileChooserParams params) {
                if (fileCallback != null) fileCallback.onReceiveValue(null);
                fileCallback = callback;
                Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("*/*");
                intent.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true);
                intent.putExtra(Intent.EXTRA_MIME_TYPES, new String[]{"image/jpeg", "image/png", "image/webp", "application/pdf", "text/*", "application/json", "application/javascript", "application/octet-stream"});
                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                try {
                    startActivityForResult(intent, PICK_FILES);
                } catch (ActivityNotFoundException error) {
                    fileCallback.onReceiveValue(null);
                    fileCallback = null;
                }
                return true;
            }
        });
        webView.setDownloadListener((url, agent, disposition, mime, length) -> openBrowser(Uri.parse(url)));
        if (state == null || webView.restoreState(state) == null) webView.loadUrl(HOME);
        if (Build.VERSION.SDK_INT >= 33) {
            getOnBackInvokedDispatcher().registerOnBackInvokedCallback(
                OnBackInvokedDispatcher.PRIORITY_DEFAULT, this::goBack);
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != PICK_FILES || fileCallback == null) return;
        Uri[] result = null;
        if (resultCode == RESULT_OK && data != null) {
            java.util.ArrayList<Uri> selected = new java.util.ArrayList<>();
            if (data.getClipData() != null) {
                for (int i = 0; i < Math.min(3, data.getClipData().getItemCount()); i++) {
                    Uri uri = data.getClipData().getItemAt(i).getUri();
                    if ("content".equals(uri.getScheme())) selected.add(uri);
                }
            } else if (data.getData() != null && "content".equals(data.getData().getScheme())) {
                selected.add(data.getData());
            }
            if (!selected.isEmpty()) result = selected.toArray(new Uri[0]);
        }
        fileCallback.onReceiveValue(result);
        fileCallback = null;
    }

    private void openBrowser(Uri uri) {
        String scheme = uri.getScheme();
        if (!"https".equals(scheme) && !"mailto".equals(scheme) && !"tel".equals(scheme)) return;
        try {
            startActivity(new Intent(Intent.ACTION_VIEW, uri).addCategory(Intent.CATEGORY_BROWSABLE));
        } catch (ActivityNotFoundException ignored) {
            android.widget.Toast.makeText(this, "No app is available to open this link.",
                android.widget.Toast.LENGTH_SHORT).show();
        }
    }

    private void goBack() {
        if (webView.canGoBack()) webView.goBack();
        else finish();
    }

    @Override
    // Android 13+ uses the registered OnBackInvokedCallback above.
    // This override supports hardware back on Android 7 through 12.
    @SuppressLint("GestureBackNavigation")
    public void onBackPressed() { goBack(); }

    @Override
    protected void onSaveInstanceState(Bundle state) {
        webView.saveState(state);
        super.onSaveInstanceState(state);
    }

    @Override
    protected void onDestroy() {
        webView.destroy();
        super.onDestroy();
    }
}

