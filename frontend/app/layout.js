import "./globals.css";
export const metadata = { title: "Pine Sales AI", description: "AI-powered sales & KDS platform" };
export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="bg-slate-50 text-slate-800 antialiased">{children}</body>
    </html>
  );
}
