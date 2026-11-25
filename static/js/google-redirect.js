"use strict";
const googleSignInLink = document.getElementById("google-signin-redirect");
if (googleSignInLink) {
  const destination = new URL(googleSignInLink.href);
  if (destination.origin === "https://accounts.google.com" &&
      destination.pathname === "/o/oauth2/v2/auth") {
    window.location.replace(destination.href);
  }
}
