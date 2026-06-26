package com.foundfilmfriend.model;

import com.google.gson.annotations.SerializedName;

public class Profile {

    @SerializedName("id")
    public String id;

    @SerializedName("display_name")
    public String displayName;

    @SerializedName("email_username")
    public String emailUsername;

    @SerializedName("birth_date")
    public String birthDate;

    public String getDisplayName() {
        if (displayName != null && !displayName.isEmpty()) return displayName;
        if (emailUsername != null && !emailUsername.isEmpty()) return emailUsername;
        return "Пользователь";
    }

    public String getInitial() {
        String name = getDisplayName();
        return name.isEmpty() ? "?" : String.valueOf(name.charAt(0)).toUpperCase();
    }
}
