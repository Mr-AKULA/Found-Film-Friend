package com.foundfilmfriend.model;

import com.google.gson.annotations.SerializedName;

public class Movie {

    @SerializedName("id")
    public int id;

    @SerializedName("name")
    public String name;

    @SerializedName("slogan")
    public String slogan;

    @SerializedName("description")
    public String description;

    @SerializedName("year")
    public int year;

    @SerializedName("age_rating")
    public int ageRating;

    @SerializedName("priority")
    public int priority;

    @SerializedName("preview_url")
    public String previewUrl;

    public String getDisplayTitle() {
        return name != null ? name : "Без названия";
    }

    public String getAgeLabel() {
        return ageRating > 0 ? ageRating + "+" : "";
    }

    public String getShortDescription() {
        if (description == null) return "";
        return description.length() > 300 ? description.substring(0, 300) + "..." : description;
    }
}
