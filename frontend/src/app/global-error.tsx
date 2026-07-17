"use client";

import * as React from "react";

/**
 * Frontière d'erreur GLOBALE (Phase 5) — dernier filet si la racine échoue.
 * Doit rendre ses propres <html>/<body> (elle remplace le layout racine).
 */
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  React.useEffect(() => {
    console.error("Erreur globale:", error);
  }, [error]);

  return (
    <html lang="fr">
      <body
        style={{
          margin: 0,
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: "system-ui, sans-serif",
          background: "#0b1017",
          color: "#e7eef4",
          padding: "24px",
        }}
      >
        <div style={{ maxWidth: "28rem", textAlign: "center" }}>
          <h2 style={{ fontSize: "1.25rem", margin: "0 0 8px" }}>
            Application indisponible
          </h2>
          <p style={{ color: "#9fb0c0", margin: "0 0 20px", lineHeight: 1.6 }}>
            Une erreur inattendue est survenue. Rechargez la page ; si le
            problème persiste, le serveur est peut-être en cours de redémarrage.
          </p>
          <button
            type="button"
            onClick={() => reset()}
            style={{
              background: "#0b6b7f",
              color: "#fff",
              border: "none",
              borderRadius: "10px",
              padding: "10px 18px",
              fontSize: "0.9rem",
              cursor: "pointer",
            }}
          >
            Recharger
          </button>
        </div>
      </body>
    </html>
  );
}
