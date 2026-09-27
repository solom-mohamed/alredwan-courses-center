"use client";

import { ChevronLeft, ChevronRight, Play } from "lucide-react";
import Image from "next/image";
import { useRef, useState } from "react";
import { useIsClient } from "usehooks-ts";
import type { Swiper as SwiperInstance } from "swiper";
import { A11y, EffectCoverflow, Keyboard, Navigation } from "swiper/modules";
import { Swiper, SwiperSlide } from "swiper/react";
import VideoLightbox, {
  isDirectVideoFile,
} from "@/components/landing-page/VideoLightbox";
import { cn, formatDuration, toHindiDigits } from "@/lib/utils";
import type { LandingVideo } from "@/types/entities";

/**
 * A cinematic "film reel" of short clips: a Swiper coverflow strip framed by
 * sprocket holes. Drag with momentum, arrows, dots and keyboard all move the
 * reel; the centred card comes forward, uploaded clips preview silently on
 * hover, and a click on the centred card opens the player.
 */
export default function VideoReel({ videos }: { videos: LandingVideo[] }) {
  const swiperRef = useRef<SwiperInstance | null>(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const [openVideo, setOpenVideo] = useState<LandingVideo | null>(null);
  // Swiper reads the DOM (RTL, sizes) while rendering, so its markup only
  // matches on the client; the server paints the first clip in the same frame.
  const isClient = useIsClient();

  const goTo = (index: number) => swiperRef.current?.slideTo(index);
  const hasMany = videos.length > 1;

  return (
    <div className="relative w-full">
      {/* Film frame */}
      <div className="bg-olive-900 tablet:rounded-[0_5rem] tablet:py-14 relative overflow-hidden rounded-[0_8rem] py-16 shadow-[0_30px_80px_-30px_rgba(46,61,56,0.7)]">
        <FilmPerforation className="top-4" />
        <FilmPerforation className="bottom-4" />

        {isClient ? (
          <Swiper
            modules={[EffectCoverflow, Navigation, Keyboard, A11y]}
            onSwiper={(instance) => {
              swiperRef.current = instance;
              // Re-measure once styles/fonts have settled so the first clip is
              // centred even when the stylesheet arrives after the first paint.
              requestAnimationFrame(() => {
                instance.update();
                instance.slideTo(0, 0);
              });
            }}
            onSlideChange={(instance) => setActiveIndex(instance.activeIndex)}
            initialSlide={0}
            effect="coverflow"
            coverflowEffect={{
              rotate: 0,
              stretch: 0,
              depth: 160,
              modifier: 1.4,
              slideShadows: false,
            }}
            centeredSlides
            slidesPerView="auto"
            spaceBetween={28}
            speed={650}
            grabCursor
            slideToClickedSlide
            // Never lock the reel: on very wide screens all clips fit in the
            // frame, and Swiper would otherwise disable arrows and dragging.
            watchOverflow={false}
            keyboard={{ enabled: true }}
            a11y={{
              containerMessage: "مقاطع من داخل الواحة",
              prevSlideMessage: "المقطع السابق",
              nextSlideMessage: "المقطع التالي",
              slideLabelMessage: "المقطع {{index}} من {{slidesLength}}",
            }}
            className="mx-auto max-w-[120rem] py-4!"
          >
            {videos.map((video, index) => (
              <SwiperSlide
                key={video.id}
                className="tablet:w-[68vw]! h-auto! w-[56rem]!"
              >
                <ReelCard
                  video={video}
                  index={index}
                  isActive={index === activeIndex}
                  onOpen={() => setOpenVideo(video)}
                />
              </SwiperSlide>
            ))}
          </Swiper>
        ) : (
          <div className="tablet:w-[68vw] mx-auto w-[56rem] py-4">
            <ReelCard
              video={videos[0]}
              index={0}
              isActive
              onOpen={() => setOpenVideo(videos[0])}
            />
          </div>
        )}

        {hasMany && (
          <>
            <ReelArrow
              side="start"
              label="المقطع السابق"
              disabled={activeIndex === 0}
              onClick={() => swiperRef.current?.slidePrev()}
            >
              <ChevronRight className="h-8 w-8" />
            </ReelArrow>
            <ReelArrow
              side="end"
              label="المقطع التالي"
              disabled={activeIndex === videos.length - 1}
              onClick={() => swiperRef.current?.slideNext()}
            >
              <ChevronLeft className="h-8 w-8" />
            </ReelArrow>
          </>
        )}
      </div>

      {/* Counter + dots */}
      {hasMany && (
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
                onClick={() => goTo(index)}
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
        "tablet:inset-x-6 pointer-events-none absolute inset-x-10 z-10 h-5 rounded-sm bg-[repeating-linear-gradient(90deg,transparent_0_1.4rem,rgba(255,255,255,0.16)_1.4rem_2.8rem)]",
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
  onOpen,
}: {
  video: LandingVideo;
  index: number;
  isActive: boolean;
  onOpen: () => void;
}) {
  const previewRef = useRef<HTMLVideoElement>(null);
  const canPreview =
    video.source === "upload" || isDirectVideoFile(video.video_url);

  const startPreview = () => {
    previewRef.current?.play().catch(() => undefined);
  };
  const stopPreview = () => {
    const el = previewRef.current;
    if (!el) return;
    el.pause();
    el.currentTime = 0;
  };

  return (
    <button
      type="button"
      aria-label={`تشغيل: ${video.title}`}
      // Swiper's slideToClickedSlide centres a side card; only the centred
      // card opens the player.
      onClick={isActive ? onOpen : undefined}
      onMouseEnter={startPreview}
      onMouseLeave={stopPreview}
      onFocus={startPreview}
      onBlur={stopPreview}
      className={cn(
        "group bg-olive-900 focus-visible:ring-beige-500 tablet:aspect-[4/5] tablet:rounded-[0_3.5rem] relative block aspect-video w-full overflow-hidden rounded-[0_5rem] text-start text-white shadow-2xl transition-opacity duration-500 ease-out focus-visible:ring-4 focus-visible:outline-none",
        isActive ? "opacity-100" : "opacity-60 hover:opacity-85",
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
