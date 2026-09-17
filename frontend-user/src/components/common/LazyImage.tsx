import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

interface LazyImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  src: string;
  alt: string;
  /** Aspect ratio class, e.g. "aspect-[3/2]". Prevents layout shift. */
  aspect?: string;
  fallback?: string;
}

function makeFallbackSvg(alt: string) {
  const safe = alt
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
  return (
    "data:image/svg+xml;utf8," +
    encodeURIComponent(
      `<svg xmlns='http://www.w3.org/2000/svg' width='480' height='320'><rect width='100%' height='100%' fill='%23131a26'/><text x='50%' y='50%' fill='%23f8fafc' font-family='sans-serif' font-size='18' text-anchor='middle' dominant-baseline='middle'>${safe}</text></svg>`,
    )
  );
}

export function LazyImage({ src, alt, aspect = "aspect-[3/2]", fallback, className, ...props }: LazyImageProps) {
  const [loaded, setLoaded] = useState(false);
  const [errored, setErrored] = useState(false);

  useEffect(() => {
    setLoaded(false);
    setErrored(false);
  }, [src]);

  const fallbackSrc = fallback ?? makeFallbackSvg(alt);

  return (
    <div className={cn("relative overflow-hidden", aspect)}>
      {!loaded && <div className="absolute inset-0 skeleton" />}
      <img
        src={errored ? fallbackSrc : src}
        alt={alt}
        loading="lazy"
        decoding="async"
        onLoad={() => setLoaded(true)}
        onError={() => {
          setErrored(true);
          setLoaded(true);
        }}
        className={cn(
          "h-full w-full object-cover transition-all duration-500",
          loaded ? "opacity-100 blur-0" : "opacity-0 blur-sm",
          className,
        )}
        {...props}
      />
    </div>
  );
}
