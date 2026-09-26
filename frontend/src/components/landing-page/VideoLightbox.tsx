"use client";

import { XIcon } from "lucide-react";
import { useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { getEmbedUrlForSource } from "@/components/dashboard/online-courses/VideoPlayer";
import type { LandingVideo } from "@/types/entities";

/** True for links that a `<video>` element can play directly. */
export function isDirectVideoFile(url: string) {
  return /\.(mp4|webm|ogv|m4v|mov)(\?.*)?$/i.test(url);
}

/**
 * Full-screen player for a landing clip. Embeds YouTube / Vimeo / Bunny
 * links in a sandboxed iframe and plays uploaded or direct files natively.
 */
export default function VideoLightbox({
  video,
  onClose,
}: {
  video: LandingVideo;
  onClose: () => void;
}) {
  const closeRef = useRef<HTMLButtonElement>(null);
  const embedUrl = getEmbedUrlForSource(video.video_url);
  const canPlayNatively =
    !embedUrl &&
    (video.source === "upload" || isDirectVideoFile(video.video_url));

  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeRef.current?.focus();

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [onClose]);

  const autoplayEmbed = embedUrl
    ? `${embedUrl}${embedUrl.includes("?") ? "&" : "?"}autoplay=1`
    : null;

  return createPortal(
    <div
      role="dialog"
      aria-modal="true"
      aria-label={video.title}
      className="motion-safe:animate-in motion-safe:fade-in-0 fixed inset-0 z-[1200] flex flex-col bg-black/95 text-white motion-safe:duration-200"
    >
      <button
        type="button"
        aria-label="إغلاق الفيديو"
        onClick={onClose}
        className="absolute inset-0 h-full w-full cursor-zoom-out"
      />

      <div className="tablet-sm:p-4 pointer-events-none relative z-10 flex items-center justify-between gap-4 p-6">
        <div className="min-w-0">
          <p className="tablet-sm:text-2xl truncate text-3xl font-bold">
            {video.title}
          </p>
          {video.description && (
            <p className="tablet-sm:text-lg truncate text-xl text-white/70">
              {video.description}
            </p>
          )}
        </div>
        <button
          ref={closeRef}
          type="button"
          onClick={onClose}
          aria-label="إغلاق"
          className="pointer-events-auto grid h-14 w-14 shrink-0 place-items-center rounded-full bg-white/10 text-white backdrop-blur-sm transition-colors hover:bg-white/25 focus-visible:ring-4 focus-visible:ring-white/70 focus-visible:outline-none"
        >
          <XIcon className="h-7 w-7" />
        </button>
      </div>

      <div className="tablet-sm:px-4 pointer-events-none relative z-10 flex min-h-0 flex-1 items-center justify-center px-16 pb-8">
        <div className="pointer-events-auto relative aspect-video w-full max-w-6xl overflow-hidden rounded-[2rem] bg-black shadow-2xl">
          {autoplayEmbed ? (
            <iframe
              src={autoplayEmbed}
              title={video.title}
              className="absolute inset-0 h-full w-full border-0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
              sandbox="allow-scripts allow-same-origin allow-presentation allow-popups allow-forms"
              referrerPolicy="strict-origin-when-cross-origin"
            />
          ) : canPlayNatively ? (
            <video
              src={video.video_url}
              poster={video.poster ?? undefined}
              controls
              autoPlay
              playsInline
              className="absolute inset-0 h-full w-full"
            >
              <track kind="captions" />
            </video>
          ) : (
            <div className="grid h-full w-full place-items-center p-6 text-center text-2xl text-white/70">
              تعذّر تشغيل هذا الفيديو، تأكد من صحة الرابط.
            </div>
          )}
        </div>
      </div>
    </div>,
    document.body,
  );
}
