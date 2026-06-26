package com.foundfilmfriend;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import com.foundfilmfriend.api.ApiClient;
import com.foundfilmfriend.api.SupabaseApi;
import com.foundfilmfriend.databinding.ActivityAuthBinding;
import com.google.gson.JsonObject;

import java.util.HashMap;
import java.util.Map;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class AuthActivity extends AppCompatActivity {

    private ActivityAuthBinding b;
    private ApiClient client;
    private boolean isLoginMode = true;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        b = ActivityAuthBinding.inflate(getLayoutInflater());
        setContentView(b.getRoot());

        client = ApiClient.getInstance(this);

        b.btnToggleMode.setOnClickListener(v -> toggleMode());
        b.btnSubmit.setOnClickListener(v -> submit());
    }

    private void toggleMode() {
        isLoginMode = !isLoginMode;
        if (isLoginMode) {
            b.tilBirthdate.setVisibility(View.GONE);
            b.btnSubmit.setText(R.string.login);
            b.btnToggleMode.setText(R.string.no_account);
        } else {
            b.tilBirthdate.setVisibility(View.VISIBLE);
            b.btnSubmit.setText(R.string.register);
            b.btnToggleMode.setText(R.string.have_account);
        }
        b.tilError.setVisibility(View.GONE);
    }

    private void submit() {
        String email = b.etEmail.getText() != null ? b.etEmail.getText().toString().trim() : "";
        String pass  = b.etPassword.getText() != null ? b.etPassword.getText().toString() : "";

        if (email.isEmpty() || pass.isEmpty()) {
            showError("Заполните все поля");
            return;
        }

        setLoading(true);

        if (isLoginMode) {
            login(email, pass);
        } else {
            String birth = b.etBirthdate.getText() != null ? b.etBirthdate.getText().toString().trim() : "";
            if (birth.isEmpty()) { showError("Укажите дату рождения"); setLoading(false); return; }
            register(email, pass, birth);
        }
    }

    private void login(String email, String pass) {
        Map<String, Object> body = new HashMap<>();
        body.put("email", email);
        body.put("password", pass);

        SupabaseApi api = client.getApi();
        api.signIn(body).enqueue(new Callback<JsonObject>() {
            @Override
            public void onResponse(Call<JsonObject> call, Response<JsonObject> resp) {
                setLoading(false);
                if (resp.isSuccessful() && resp.body() != null) {
                    JsonObject json = resp.body();
                    String token = json.get("access_token").getAsString();
                    String uid   = json.getAsJsonObject("user").get("id").getAsString();
                    client.saveSession(token, uid);
                    goToMain();
                } else {
                    showError("Неверный email или пароль");
                }
            }
            @Override
            public void onFailure(Call<JsonObject> call, Throwable t) {
                setLoading(false);
                showError("Ошибка сети: " + t.getMessage());
            }
        });
    }

    private void register(String email, String pass, String birthDate) {
        Map<String, Object> meta = new HashMap<>();
        meta.put("birth_date", birthDate);

        Map<String, Object> body = new HashMap<>();
        body.put("email", email);
        body.put("password", pass);
        body.put("data", meta);

        SupabaseApi api = client.getApi();
        api.signUp(body).enqueue(new Callback<JsonObject>() {
            @Override
            public void onResponse(Call<JsonObject> call, Response<JsonObject> resp) {
                setLoading(false);
                if (resp.isSuccessful() && resp.body() != null) {
                    JsonObject json = resp.body();
                    if (json.has("access_token")) {
                        String token = json.get("access_token").getAsString();
                        String uid   = json.getAsJsonObject("user").get("id").getAsString();
                        client.saveSession(token, uid);

                        /* Update profile with birth_date */
                        Map<String, Object> profileBody = new HashMap<>();
                        profileBody.put("id", uid);
                        profileBody.put("birth_date", birthDate);
                        api.upsertProfile(client.getBearerToken(), profileBody).enqueue(new Callback<Void>() {
                            @Override public void onResponse(Call<Void> c, Response<Void> r) { goToMain(); }
                            @Override public void onFailure(Call<Void> c, Throwable t) { goToMain(); }
                        });
                    } else {
                        showError("Проверьте почту для подтверждения");
                    }
                } else {
                    showError("Ошибка регистрации. Возможно, email уже занят.");
                }
            }
            @Override
            public void onFailure(Call<JsonObject> call, Throwable t) {
                setLoading(false);
                showError("Ошибка сети: " + t.getMessage());
            }
        });
    }

    private void goToMain() {
        String inviteId = getIntent().getStringExtra("invite_id");
        Intent i = new Intent(this, MainActivity.class);
        if (inviteId != null) i.putExtra("invite_id", inviteId);
        startActivity(i);
        finish();
    }

    private void showError(String msg) {
        b.tvError.setText(msg);
        b.tilError.setVisibility(View.VISIBLE);
    }

    private void setLoading(boolean loading) {
        b.btnSubmit.setEnabled(!loading);
        b.progressBar.setVisibility(loading ? View.VISIBLE : View.GONE);
    }
}
