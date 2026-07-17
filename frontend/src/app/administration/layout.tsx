import { AdminNav } from "@/components/admin/admin-nav";

export default function AdministrationLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-6">
      <AdminNav />
      {children}
    </div>
  );
}
