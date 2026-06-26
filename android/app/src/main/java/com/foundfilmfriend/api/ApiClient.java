package com.foundfilmfriend.api;

import android.content.Context;
import android.content.SharedPreferences;

import androidx.security.crypto.EncryptedSharedPreferences;
import androidx.security.crypto.MasterKey;

import com.foundfilmfriend.BuildConfig;

import java.io.IOException;

import okhttp3.Interceptor;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import okhttp3.logging.HttpLoggingInterceptor;
import retrofit2.Retrofit;
import retrofit2.converter.gson.GsonConverterFactory;

public class ApiClient {

    private static ApiClient instance;
    private final SupabaseApi api;
    private SharedPreferences prefs;

    private String accessToken = null;
    private String userId = null;

    private ApiClient(Context context) {
        try {
            MasterKey masterKey = new MasterKey.Builder(context)
                .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
                .build();
            prefs = EncryptedSharedPreferences.create(
                context,
                "fff_secure_prefs",
                masterKey,
                EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
                EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
            );
        } catch (Exception e) {
            prefs = context.getSharedPreferences("fff_prefs", Context.MODE_PRIVATE);
        }

        /* Restore saved session */
        accessToken = prefs.getString("access_token", null);
        userId      = prefs.getString("user_id", null);

        HttpLoggingInterceptor logging = new HttpLoggingInterceptor();
        logging.setLevel(BuildConfig.DEBUG
            ? HttpLoggingInterceptor.Level.BODY
            : HttpLoggingInterceptor.Level.NONE);

        OkHttpClient client = new OkHttpClient.Builder()
            .addInterceptor(logging)
            .addInterceptor(new ApiKeyInterceptor())
            .build();

        Retrofit retrofit = new Retrofit.Builder()
            .baseUrl(BuildConfig.SUPABASE_URL + "/")
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build();

        api = retrofit.create(SupabaseApi.class);
    }

    public static synchronized ApiClient getInstance(Context context) {
        if (instance == null) instance = new ApiClient(context.getApplicationContext());
        return instance;
    }

    public SupabaseApi getApi() { return api; }

    public String getBearerToken() {
        return accessToken != null ? "Bearer " + accessToken : "Bearer " + BuildConfig.SUPABASE_ANON_KEY;
    }

    public String getUserId() { return userId; }

    public boolean isLoggedIn() { return accessToken != null && userId != null; }

    public void saveSession(String token, String uid) {
        accessToken = token;
        userId      = uid;
        prefs.edit().putString("access_token", token).putString("user_id", uid).apply();
    }

    public void clearSession() {
        accessToken = null;
        userId      = null;
        prefs.edit().remove("access_token").remove("user_id").apply();
    }

    /* Adds apikey header to every request */
    private class ApiKeyInterceptor implements Interceptor {
        @Override
        public Response intercept(Chain chain) throws IOException {
            Request req = chain.request().newBuilder()
                .addHeader("apikey", BuildConfig.SUPABASE_ANON_KEY)
                .build();
            return chain.proceed(req);
        }
    }
}
