/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    // Le monorepo partage `../shared` (hors du dossier frontend) : on autorise
    // les imports de fichiers situés en dehors de la racine du projet.
    externalDir: true,
    optimizePackageImports: ["lucide-react", "framer-motion"],
  },
  async rewrites() {
    // Proxy optionnel vers l'API en développement (évite les soucis CORS).
    const apiUrl = process.env.BACKEND_INTERNAL_URL;
    if (!apiUrl) return [];
    return [{ source: "/api/:path*", destination: `${apiUrl}/api/:path*` }];
  },
};

export default nextConfig;
