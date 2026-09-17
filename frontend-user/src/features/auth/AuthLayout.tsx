import { Link } from "react-router-dom";

export function AuthLayout({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}) {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="relative hidden overflow-hidden lg:block">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/20 via-accent/10 to-background" />
        <div className="relative flex h-full flex-col justify-between p-12">
          <Link to="/" className="flex items-center gap-2 text-xl font-bold">
            <span className="grid h-9 w-9 place-items-center rounded-lg bg-primary text-primary-foreground">S</span>
            SportX
          </Link>
          <div>
            <h2 className="max-w-md text-4xl font-extrabold leading-tight">
              The premium sports & games dashboard.
            </h2>
            <p className="mt-4 max-w-sm text-muted-foreground">
              Live events, a dynamic game catalogue, and a full virtual wallet — all in one modern
              experience.
            </p>
          </div>
          <p className="text-xs text-muted-foreground">Virtual credits · Entertainment simulation only.</p>
        </div>
      </div>

      <div className="flex items-center justify-center p-6">
        <div className="w-full max-w-sm">
          <div className="mb-8">
            <h1 className="text-2xl font-bold">{title}</h1>
            <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>
          </div>
          {children}
          {footer && <div className="mt-6 text-center text-sm text-muted-foreground">{footer}</div>}
        </div>
      </div>
    </div>
  );
}
