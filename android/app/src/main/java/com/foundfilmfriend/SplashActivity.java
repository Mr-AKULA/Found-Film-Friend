package com.foundfilmfriend;

import android.content.Intent;
import android.os.Bundle;

import androidx.appcompat.app.AppCompatActivity;

import com.foundfilmfriend.api.ApiClient;

public class SplashActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        ApiClient client = ApiClient.getInstance(this);

        /* Handle deep-link invite: foundfilmfriend://invite?id=UUID */
        String inviteId = null;
        Intent intent = getIntent();
        if (intent != null && intent.getData() != null) {
            inviteId = intent.getData().getQueryParameter("id");
        }

        Intent next;
        if (client.isLoggedIn()) {
            next = new Intent(this, MainActivity.class);
        } else {
            next = new Intent(this, AuthActivity.class);
        }

        if (inviteId != null) {
            next.putExtra("invite_id", inviteId);
        }

        startActivity(next);
        finish();
    }
}
