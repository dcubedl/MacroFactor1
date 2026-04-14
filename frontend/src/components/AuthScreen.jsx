import { useState } from "react";
import { api } from "../services/api";
import AppIcon from "./AppIcon";

/**
 * Login / signup screen shown before the main app.
 *
 * Props
 * -----
 * onSuccess(authData, isNewUser)
 *   Called after a successful auth.
 *   authData  — the AuthResponse from the backend ({ user_id, email, ... })
 *   isNewUser — true after signup (caller should show onboarding)
 *               false after login  (caller should go to home)
 */
export default function AuthScreen({ onSuccess }) {
  const [mode, setMode]         = useState("login"); // "login" | "signup"
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState(null);

  const clearError = () => setError(null);

  const switchMode = (m) => { setMode(m); clearError(); };

  const validate = () => {
    if (!email.trim())    { setError("Please enter your email address."); return false; }
    if (!password)        { setError("Please enter a password."); return false; }
    if (password.length < 6) { setError("Password must be at least 6 characters."); return false; }
    return true;
  };

  const submit = async () => {
    if (!validate()) return;
    setLoading(true);
    clearError();

    try {
      if (mode === "login") {
        const data = await api.login(email.trim(), password);
        onSuccess(data, false);
      } else {
        const data = await api.signup(email.trim(), password);
        if (data.requires_confirmation) {
          setError("Check your inbox for a confirmation email, then sign in.");
          return;
        }
        onSuccess(data, true);
      }
    } catch (err) {
      const status = err.status;
      const msg =
        status === 0   ? "Cannot reach the server. Is the backend running?" :
        status === 400 ? (mode === "login" ? "Invalid email or password." : err.message) :
        status === 422 ? "Invalid email format." :
        status === 429 ? "Too many attempts — please wait a moment." :
        err.message    || "Something went wrong. Please try again.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const onKey = (e) => { if (e.key === "Enter" && !loading) submit(); };

  // ---- Styles (inline, matching the app's dark theme) ---------------------
  const inp = {
    background: "var(--card)",
    border: "1px solid var(--bdr)",
    borderRadius: 14,
    color: "var(--t1)",
    fontSize: 16,
    padding: "16px 18px",
    width: "100%",
    outline: "none",
    fontFamily: "var(--fd)",
    boxSizing: "border-box",
    transition: "border-color .15s",
  };

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      flexDirection: "column",
      justifyContent: "center",
      padding: "40px 24px 60px",
      animation: "popIn .4s cubic-bezier(0.22,1.2,.36,1) both",
    }}>

      {/* Logo + title */}
      <div style={{ textAlign: "center", marginBottom: 36 }}>
        <AppIcon size={72} />
        <h1 style={{
          fontSize: 26, fontWeight: 900, letterSpacing: "-.03em",
          marginTop: 16, marginBottom: 6,
        }}>
          MacroRanked
        </h1>
        <p style={{ fontSize: 13, color: "var(--t3)", fontFamily: "var(--fm)" }}>
          Track your meals. Earn your rank.
        </p>
      </div>

      {/* Mode toggle */}
      <div style={{
        display: "flex", background: "var(--card)", borderRadius: 14,
        padding: 4, marginBottom: 24, border: "1px solid var(--bdr)",
      }}>
        {["login", "signup"].map(m => (
          <button
            key={m}
            onClick={() => switchMode(m)}
            style={{
              flex: 1, padding: "10px 0", border: "none", borderRadius: 10,
              background: mode === m ? "var(--acc)" : "transparent",
              color:      mode === m ? "#fff"       : "var(--t3)",
              fontSize: 13, fontWeight: 700, cursor: "pointer",
              fontFamily: "var(--fm)", letterSpacing: ".05em",
              textTransform: "uppercase", transition: "all .15s",
              boxShadow: mode === m ? "0 0 16px var(--accG)" : "none",
            }}>
            {m === "login" ? "Sign In" : "Create Account"}
          </button>
        ))}
      </div>

      {/* Inputs */}
      <div style={{ display: "flex", flexDirection: "column", gap: 12, marginBottom: error ? 12 : 20 }}>
        <input
          type="email"
          placeholder="Email address"
          value={email}
          onChange={e => { setEmail(e.target.value); clearError(); }}
          onKeyDown={onKey}
          style={inp}
          autoCapitalize="none"
          autoCorrect="off"
          autoComplete="email"
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={e => { setPassword(e.target.value); clearError(); }}
          onKeyDown={onKey}
          style={inp}
          autoComplete={mode === "login" ? "current-password" : "new-password"}
        />
      </div>

      {/* Error banner */}
      {error && (
        <div style={{
          background: "rgba(255,23,68,.08)", border: "1px solid rgba(255,23,68,.25)",
          borderRadius: 12, padding: "12px 16px", marginBottom: 16,
          fontSize: 13, color: "var(--acc)", lineHeight: 1.6,
        }}>
          {error}
        </div>
      )}

      {/* Primary button */}
      <button
        onClick={submit}
        disabled={loading}
        style={{
          width: "100%", padding: "16px 0", border: "none", borderRadius: 14,
          background:  loading ? "var(--elev)" : "var(--acc)",
          color:       loading ? "var(--t3)"   : "#fff",
          fontSize: 16, fontWeight: 800, letterSpacing: "-.01em",
          cursor:      loading ? "default" : "pointer",
          boxShadow:   loading ? "none" : "0 0 32px var(--accG)",
          transition: "all .15s",
          marginBottom: 20,
        }}>
        {loading
          ? "Please wait…"
          : mode === "login" ? "Sign In" : "Create Account"}
      </button>

      {/* Switch mode link */}
      <p style={{ textAlign: "center", fontSize: 12, color: "var(--t3)", fontFamily: "var(--fm)" }}>
        {mode === "login" ? "No account yet?" : "Already have an account?"}{" "}
        <button
          onClick={() => switchMode(mode === "login" ? "signup" : "login")}
          style={{
            background: "none", border: "none", color: "var(--acc)",
            cursor: "pointer", fontSize: 12, fontFamily: "var(--fm)",
            fontWeight: 700, padding: 0,
          }}>
          {mode === "login" ? "Create one →" : "Sign in →"}
        </button>
      </p>
    </div>
  );
}
