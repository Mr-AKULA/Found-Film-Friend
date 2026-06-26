package com.foundfilmfriend.api;

import com.foundfilmfriend.model.Movie;
import com.foundfilmfriend.model.Profile;
import com.google.gson.JsonObject;

import java.util.List;
import java.util.Map;

import retrofit2.Call;
import retrofit2.http.Body;
import retrofit2.http.GET;
import retrofit2.http.Header;
import retrofit2.http.Headers;
import retrofit2.http.PATCH;
import retrofit2.http.POST;
import retrofit2.http.Query;

public interface SupabaseApi {

    /* ── AUTH ─────────────────────────────────────────── */

    @POST("auth/v1/signup")
    @Headers("Content-Type: application/json")
    Call<JsonObject> signUp(@Body Map<String, Object> body);

    @POST("auth/v1/token?grant_type=password")
    @Headers("Content-Type: application/json")
    Call<JsonObject> signIn(@Body Map<String, Object> body);

    @POST("auth/v1/logout")
    Call<Void> signOut(@Header("Authorization") String bearer);

    /* ── PROFILES ─────────────────────────────────────── */

    @GET("rest/v1/profiles")
    Call<List<Profile>> getProfile(
        @Header("Authorization") String bearer,
        @Query("id")     String eq,
        @Query("select") String select
    );

    @POST("rest/v1/profiles")
    @Headers({
        "Content-Type: application/json",
        "Prefer: resolution=merge-duplicates"
    })
    Call<Void> upsertProfile(
        @Header("Authorization") String bearer,
        @Body Map<String, Object> body
    );

    /* ── MOVIES (RPC) ─────────────────────────────────── */

    @POST("rest/v1/rpc/get_next_movie")
    @Headers("Content-Type: application/json")
    Call<List<Movie>> getNextMovie(
        @Header("Authorization") String bearer,
        @Body Map<String, String> body
    );

    /* ── ACTIONS ──────────────────────────────────────── */

    @POST("rest/v1/actions")
    @Headers({
        "Content-Type: application/json",
        "Prefer: resolution=merge-duplicates"
    })
    Call<Void> upsertAction(
        @Header("Authorization") String bearer,
        @Body Map<String, Object> body
    );

    @GET("rest/v1/actions")
    Call<List<JsonObject>> getLikedMovies(
        @Header("Authorization") String bearer,
        @Query("user_id")       String eq,
        @Query("want_to_watch") String filter,
        @Query("select")        String select,
        @Query("order")         String order
    );

    @PATCH("rest/v1/actions")
    @Headers("Content-Type: application/json")
    Call<Void> updateAction(
        @Header("Authorization") String bearer,
        @Query("user_id")  String userEq,
        @Query("movie_id") String movieEq,
        @Body Map<String, Object> body
    );

    /* ── FRIENDS ──────────────────────────────────────── */

    @GET("rest/v1/friends")
    Call<List<JsonObject>> getFriends(
        @Header("Authorization") String bearer,
        @Query("or")     String filter,
        @Query("status") String eq,
        @Query("select") String select
    );

    @POST("rest/v1/friends")
    @Headers({
        "Content-Type: application/json",
        "Prefer: resolution=merge-duplicates"
    })
    Call<Void> addFriend(
        @Header("Authorization") String bearer,
        @Body Map<String, Object> body
    );
}
