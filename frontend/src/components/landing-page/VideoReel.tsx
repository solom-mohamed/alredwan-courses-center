"use client";

import { ChevronLeft, ChevronRight, Play } from "lucide-react";
import Image from "next/image";
import { useCallback, useEffect, useRef, useState } from "react";
import VideoLightbox, {
  isDirectVideoFile,
} from "@/components/landing-page/VideoLightbox";
import { cn, formatDuration, toHindiDigits } from "@/lib/utils";
import type { LandingVideo } from "@/types/entities";

/**
 * A cinematic "film reel" of short clips: cards snap to the centre of a
 * horizontal strip framed by sprocket holes, the centred card comes forward,
 * uploaded clips preview silently on hover, and a click opens the player.
 */
export default function VideoReel({ videos }: { videos: LandingVideo[] }) {
  const trackRef = useRef<HTMLDivElement>(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const [openVideo, setOpenVideo] = useState<LandingVideo | null>(null);

  // The card whose centre is closest to the strip's centre is "active".
  const syncActive = useCallback(() => {
    const track = trackRef.current;
    if (!track) return;
    const centre = track.scrollLeft + track.clientWidth / 2;
    let best = 0;
    let bestDistance = Number.POSITIVE_INFINITY;
    Array.from(track.children).forEach((child, index) => {
      const el = child as HTMLElement;
      const cardCentre = el.offsetLeft + el.offsetWidth / 2;
      const distance = Math.abs(cardCentre - centre);
      if (distance < bestDistance) {
        bestDistance = distance;
        best = index;
      }
    });
    setActiveIndex(best);
  }, []);

  useEffect(() => {
    const track = trackRef.current;
    if (!track) return;
    let frame = 0;
    const onScroll = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(syncActive);
    };
    track.addEventListener("scroll", onScroll, { passive: true });
    // Measure once mounted (next frame) so the first card is marked active.
    frame = requestAnimationFrame(syncActive);
    return () => {
      track.removeEventListener("scroll", onScroll);
      cancelAnimationFrame(frame);
    };
  }, [syncActive]);

  const scrollToIndex = (index: number) => {
    const track = trackRef.current;
    const card = track?.children[index] as HTMLElement | undefined;
    if (!track || !card) return;
    track.scrollTo({
      left: card.offsetLeft + card.offsetWidth / 2 - track.clientWidth / 2,
      behavior: "smooth",
    });
  };

  const step = (delta: number) => {
    const next = Math.min(videos.length - 1, Math.max(0, activeIndex + delta));
    scrollToIndex(next);
  };

  const onKeyDown = (event: React.KeyboardEvent) => {
    // RTL page: ArrowRight goes to the previous clip, ArrowLeft to the next.
    if (event.key === "ArrowLeft") step(1);
    if (event.key === "ArrowRight") step(-1);
  };

  return (
    <div className="relative w-full">
      {/* Film frame */}
      <div className="bg-olive-900 tablet:rounded-[0_5rem] tablet:py-14 relative overflow-hidden rounded-[0_8rem] py-16 shadow-[0_30px_80px_-30px_rgba(46,61,56,0.7)]">
        <FilmPerforation className="top-4" />
        <FilmPerforation className="bottom-4" />

        <div
          ref={trackRef}
          role="listbox"
          aria-label="مقاطع من داخل الواحة"
          aria-activedescendant={`landing-clip-${videos[activeIndex]?.id}`}
          tabIndex={0}
          onKeyDown={onKeyDown}
          className="no-scrollbar focus-visible:ring-beige-500/70 tablet:gap-6 tablet:px-[16vw] flex snap-x snap-mandatory gap-8 overflow-x-auto scroll-smooth px-[26%] py-4 outline-none focus-visible:ring-4"
        >
          {videos.map((video, index) => (
            <ReelCard
              key={video.id}
              video={video}
              index={index}
              isActive={index === activeIndex}
              onFocusCard={() => scrollToIndex(index)}
              onOpen={() => setOpenVideo(video)}
            />
          ))}
        </div>

        {videos.length > 1 && (
          <>
            <ReelArrow
              side="start"
              label="المقطع السابق"
              disabled={activeIndex === 0}
              onClick={() => step(-1)}
            >
              <ChevronRight className="h-8 w-8" />
            </ReelArrow>
            <ReelArrow
              side="end"
              label="المقطع التالي"
              disabled={activeIndex === videos.length - 1}
              onClick={() => step(1)}
            >
              <ChevronLeft className="h-8 w-8" />
            </ReelArrow>
          </>
        )}
      </div>

      {/* Counter + dots */}
      {videos.length > 1 && (
        <div className="mt-8 flex items-center justify-center gap-4">
          <span className="text-olive-700 text-xl font-bold tabular-nums">
            {toHindiDigits(activeIndex + 1)} / {toHindiDigits(videos.length)}
          </span>
          <div className="flex items-center gap-2">
            {videos.map((video, index) => (
              <button
                key={video.id}
                type="button"
                aria-label={`الانتقال إلى: ${video.title}`}
                aria-current={index === activeIndex ? "true" : undefined}
                onClick={() => scrollToIndex(index)}
                className={cn(
                  "h-3 rounded-full transition-all duration-300",
                  index === activeIndex
                    ? "bg-beige-500 w-10"
                    : "bg-olive-300/50 hover:bg-olive-400 w-3",
                )}
              />
            ))}
          </div>
        </div>
      )}

      {openVideo && (
        <VideoLightbox video={openVideo} onClose={() => setOpenVideo(null)} />
      )}
    </div>
  );
}

function FilmPerforation({ className }: { className?: string }) {
  return (
    <div
      aria-hidden
      className={cn(
        "tablet:inset-x-6 pointer-events-none absolute inset-x-10 h-5 rounded-sm bg-[repeating-linear-gradient(90deg,transparent_0_1.4rem,rgba(255,255,255,0.16)_1.4rem_2.8rem)]",
        className,
      )}
    />
  );
}

function ReelArrow({
  side,
  label,
  disabled,
  onClick,
  children,
}: {
  side: "start" | "end";
  label: string;
  disabled: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      disabled={disabled}
      onClick={onClick}
      className={cn(
        "tablet-sm:hidden hover:bg-beige-500 hover:text-olive-900 focus-visible:ring-beige-500/70 absolute top-1/2 z-20 grid h-16 w-16 -translate-y-1/2 place-items-center rounded-full bg-white/10 text-white backdrop-blur-md transition-all focus-visible:ring-4 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-30",
        side === "start" ? "start-6" : "end-6",
      )}
    >
      {children}
    </button>
  );
}

function ReelCard({
  video,
  index,
  isActive,
  onFocusCard,
  onOpen,
}: {
  video: LandingVideo;
  index: number;
  isActive: boolean;
  onFocusCard: () => void;
  onOpen: () => void;
}) {
  const previewRef = useRef<HTMLVideoElement>(null);
  const canPreview =
    video.source === "upload" || isDirectVideoFile(video.video_url);

  const startPreview = () => {
    const el = previewRef.current;
    if (!el) return;
    el.play().catch(() => undefined);
  };
  const stopPreview = () => {
    const el = previewRef.current;
    if (!el) return;
    el.pause();
    el.currentTime = 0;
  };

  return (
    <button
      id={`landing-clip-${video.id}`}
      type="button"
      role="option"
      aria-selected={isActive}
      aria-label={`تشغيل: ${video.title}`}
      onClick={isActive ? onOpen : onFocusCard}
      onMouseEnter={startPreview}
      onMouseLeave={stopPreview}
      onFocus={startPreview}
      onBlur={stopPreview}
      className={cn(
        "group bg-olive-900 focus-visible:ring-beige-500 tablet:aspect-[4/5] tablet:w-[68vw] tablet:rounded-[0_3.5rem] relative aspect-video w-[56rem] shrink-0 snap-center overflow-hidden rounded-[0_5rem] text-start text-white shadow-2xl transition-all duration-500 ease-out focus-visible:ring-4 focus-visible:outline-none",
        isActive
          ? "scale-100 opacity-100"
          : "scale-[0.86] opacity-55 hover:opacity-80",
      )}
    >
      {video.poster ? (
        <Image
          src={video.poster}
          alt=""
          fill
          unoptimized
          sizes="(max-width: 900px) 68vw, 56rem"
          className="object-cover transition-transform duration-700 group-hover:scale-105"
          draggable="false"
        />
      ) : (
        <div className="from-olive-500 to-olive-900 absolute inset-0 bg-gradient-to-br" />
      )}

      {canPreview && (
        <video
          ref={previewRef}
          src={video.video_url}
          muted
          loop
          playsInline
          preload="none"
          aria-hidden
          className="absolute inset-0 h-full w-full object-cover opacity-0 transition-opacity duration-500 group-hover:opacity-100 group-focus-visible:opacity-100"
        />
      )}

      <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(46,61,56,0)_35%,rgba(46,61,56,0.92)_100%)]" />

      <span className="absolute start-5 top-5 rounded-full bg-black/45 px-4 py-1.5 text-lg font-semibold backdrop-blur-sm">
        {toHindiDigits(index + 1)}
      </span>
      {video.duration_seconds > 0 && (
        <span
          dir="ltr"
          className="bg-beige-500/95 text-olive-900 absolute end-5 top-5 rounded-full px-4 py-1.5 text-lg font-bold tabular-nums"
        >
          {formatDuration(video.duration_seconds, "clock")}
        </span>
      )}

      <span
        className={cn(
          "bg-beige-500 text-olive-900 absolute top-1/2 left-1/2 flex h-24 w-24 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full shadow-[0_10px_40px_rgba(0,0,0,0.35)] transition-all duration-300 group-hover:scale-110",
          isActive ? "opacity-100" : "opacity-0",
        )}
      >
        <Play className="ms-1 h-10 w-10 fill-current" />
      </span>

      <span className="tablet:p-7 absolute inset-x-0 bottom-0 flex flex-col gap-2 p-9">
        <span className="tablet:text-[2.2rem] line-clamp-2 text-[2.8rem] leading-tight font-black">
          {video.title}
        </span>
        {video.description && (
          <span className="tablet:text-[1.5rem] line-clamp-2 text-[1.7rem] text-gray-100/85">
            {video.description}
          </span>
        )}
      </span>
    </button>
  );
}
