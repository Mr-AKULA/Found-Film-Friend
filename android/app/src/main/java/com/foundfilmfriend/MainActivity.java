package com.foundfilmfriend;

import android.animation.AnimatorSet;
import android.animation.ObjectAnimator;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;
import androidx.fragment.app.Fragment;

import com.bumptech.glide.Glide;
import com.foundfilmfriend.api.ApiClient;
import com.foundfilmfriend.api.SupabaseApi;
import com.foundfilmfriend.databinding.ActivityMainBinding;
import com.foundfilmfriend.fragment.BrowseFragment;
import com.foundfilmfriend.fragment.FriendsFragment;
import com.foundfilmfriend.fragment.WatchlistFragment;
import com.foundfilmfriend.model.Movie;
import com.google.android.material.dialog.MaterialAlertDialogBuilder;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class MainActivity extends AppCompatActivity {

    private ActivityMainBinding b;
    private ApiClient client;

    private Movie currentMovie;
    private boolean isAnimating = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        b = ActivityMainBinding.inflate(getLayoutInflater());
        setContentView(b.getRoot());

        client = ApiClient.getInstance(this);

        setupNavigation();
        showBrowse();

        /* Handle friend invite */
        String inviteId = getIntent().getStringExtra("invite_id");
        if (inviteId != null && !inviteId.equals(client.getUserId())) {
            showFriendInviteDialog(inviteId);
        }
    }

    /* ─── NAVIGATION ─────────────────────────── */

    private void setupNavigation() {
        b.bottomNav.setOnItemSelectedListener(item -> {
            int id = item.getItemId();
            if (id == R.id.nav_browse) {
                showBrowse();
            } else if (id == R.id.nav_watchlist) {
                showFragment(new WatchlistFragment());
            } else if (id == R.id.nav_friends) {
                FriendsFragment f = new FriendsFragment();
                f.setShareUrl(buildInviteUrl());
                showFragment(f);
            }
            return true;
        });
    }

    private void showFragment(Fragment fragment) {
        getSupportFragmentManager().beginTransaction()
            .replace(R.id.fragment_container, fragment)
            .commit();
        b.browseContainer.setVisibility(View.GONE);
        b.fragmentContainer.setVisibility(View.VISIBLE);
    }

    private void showBrowse() {
        b.fragmentContainer.setVisibility(View.GONE);
        b.browseContainer.setVisibility(View.VISIBLE);
        if (currentMovie == null) loadNextMovie();
        setupCardActions();
    }

    /* ─── MOVIE BROWSE ───────────────────────── */

    public void loadNextMovie() {
        showLoading(true);
        Map<String, String> body = new HashMap<>();
        body.put("p_user_id", client.getUserId());

        client.getApi().getNextMovie(client.getBearerToken(), body)
            .enqueue(new Callback<List<Movie>>() {
                @Override
                public void onResponse(Call<List<Movie>> call, Response<List<Movie>> resp) {
                    showLoading(false);
                    if (resp.isSuccessful() && resp.body() != null && !resp.body().isEmpty()) {
                        currentMovie = resp.body().get(0);
                        bindMovie(currentMovie);
                    } else {
                        showEmpty(true);
                    }
                }
                @Override
                public void onFailure(Call<List<Movie>> call, Throwable t) {
                    showLoading(false);
                    Toast.makeText(MainActivity.this, "Ошибка сети", Toast.LENGTH_SHORT).show();
                }
            });
    }

    private void bindMovie(Movie movie) {
        showEmpty(false);
        b.cardContainer.setVisibility(View.VISIBLE);

        b.tvMovieTitle.setText(movie.getDisplayTitle());
        b.tvMovieYear.setText(String.valueOf(movie.year));
        b.tvAgeRating.setText(movie.getAgeLabel());
        b.tvMovieTagline.setText(movie.slogan != null ? movie.slogan : "");
        b.tvMovieDesc.setText(movie.getShortDescription());

        b.tvMovieTagline.setVisibility(movie.slogan != null ? View.VISIBLE : View.GONE);
        b.tvAgeRating.setVisibility(movie.ageRating > 0 ? View.VISIBLE : View.GONE);

        if (movie.previewUrl != null && !movie.previewUrl.isEmpty()) {
            Glide.with(this)
                .load(movie.previewUrl)
                .centerCrop()
                .placeholder(R.drawable.placeholder_poster)
                .into(b.ivMoviePoster);
        } else {
            b.ivMoviePoster.setImageResource(R.drawable.placeholder_poster);
        }

        /* Animate card in */
        b.cardContainer.setAlpha(0f);
        b.cardContainer.setScaleX(0.9f);
        b.cardContainer.setScaleY(0.9f);
        b.cardContainer.animate()
            .alpha(1f).scaleX(1f).scaleY(1f)
            .setDuration(300)
            .setInterpolator(new android.view.animation.OvershootInterpolator(1.2f))
            .start();
    }

    private void setupCardActions() {
        b.btnLike.setOnClickListener(v -> rateMovie(true));
        b.btnDislike.setOnClickListener(v -> rateMovie(false));
    }

    public void rateMovie(boolean liked) {
        if (currentMovie == null || isAnimating) return;
        isAnimating = true;

        /* Visual feedback */
        int dx = liked ? 800 : -800;
        float rot = liked ? 15f : -15f;

        b.cardContainer.animate()
            .translationX(dx)
            .rotation(rot)
            .alpha(0f)
            .setDuration(300)
            .withEndAction(() -> {
                saveAction(currentMovie.id, liked);
                currentMovie = null;
                b.cardContainer.setTranslationX(0);
                b.cardContainer.setRotation(0);
                b.cardContainer.setAlpha(1f);
                isAnimating = false;
                loadNextMovie();
            })
            .start();
    }

    private void saveAction(int movieId, boolean liked) {
        Map<String, Object> body = new HashMap<>();
        body.put("user_id",       client.getUserId());
        body.put("movie_id",      movieId);
        body.put("want_to_watch", liked);

        client.getApi().upsertAction(client.getBearerToken(), body)
            .enqueue(new Callback<Void>() {
                @Override public void onResponse(Call<Void> c, Response<Void> r) {}
                @Override public void onFailure(Call<Void> c, Throwable t) {}
            });
    }

    /* ─── FRIENDS INVITE ─────────────────────── */

    private String buildInviteUrl() {
        return "foundfilmfriend://invite?id=" + client.getUserId();
    }

    private void showFriendInviteDialog(String friendId) {
        new MaterialAlertDialogBuilder(this)
            .setTitle("Приглашение в друзья")
            .setMessage("Хотите добавить пользователя в друзья?")
            .setPositiveButton("Добавить", (d, w) -> addFriend(friendId))
            .setNegativeButton("Пропустить", null)
            .show();
    }

    private void addFriend(String friendId) {
        Map<String, Object> body = new HashMap<>();
        body.put("user_one", client.getUserId());
        body.put("user_two", friendId);
        body.put("status",   1);

        client.getApi().addFriend(client.getBearerToken(), body)
            .enqueue(new Callback<Void>() {
                @Override
                public void onResponse(Call<Void> c, Response<Void> r) {
                    Toast.makeText(MainActivity.this, "Друг добавлен! 👥", Toast.LENGTH_SHORT).show();
                }
                @Override
                public void onFailure(Call<Void> c, Throwable t) {}
            });
    }

    /* ─── UI HELPERS ─────────────────────────── */

    private void showLoading(boolean show) {
        b.progressBar.setVisibility(show ? View.VISIBLE : View.GONE);
        if (show) b.cardContainer.setVisibility(View.GONE);
    }

    private void showEmpty(boolean show) {
        b.layoutEmpty.setVisibility(show ? View.VISIBLE : View.GONE);
        b.cardContainer.setVisibility(show ? View.GONE : View.VISIBLE);
    }
}
