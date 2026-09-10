"use client";

import { Play } from "lucide-react";
import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import type { LandingVideo } from "@/dev-data/videos";
import { cn } from "@/lib/utils";

export default function VideoShowcase({ videos }: { videos: LandingVideo[] }) {
  const [active, setActive] = useState<LandingVideo>(videos[0]);
  const [isPlaying, setIsPlaying] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  // Start playback once the user picks a clip (deferred until the <video> re-mounts)
  useEffect(() => {
    if (!isPlaying) return;
    videoRef.current?.play().catch(() => setIsPlaying(false));
  }, [isPlaying, active.id]);

  function play(video: LandingVideo) {
    setActive(video);
    setIsPlaying(true);
  }

  return (
    <div className="tablet:grid-cols-1 grid w-full grid-cols-[1.65fr_1fr] gap-10">
      {/* Featured player */}
      <div className="shadow-primary tablet:rounded-[0_6rem] bg-olive-900 relative aspect-video w-full overflow-hidden rounded-[0_10rem]">
        <video
          key={active.id}
          ref={videoRef}
          src={active.src}
          poster={active.poster}
          preload="none"
          playsInline
          controls={isPlaying}
          onEnded={() => setIsPlaying(false)}
          className="h-full w-full object-cover"
        />

        {!isPlaying && (
          <button
            type="button"
            onClick={() => play(active)}
            aria-label={`تشغيل: ${active.title}`}
            className="group absolute inset-0 flex cursor-pointer flex-col items-center justify-center bg-[linear-gradient(180deg,rgba(46,61,56,0)_30%,rgba(46,61,56,0.85)_100%)] text-gray-100"
          >
            <span className="tablet:h-20 tablet:w-20 bg-beige-500/95 shadow-soft flex h-28 w-28 items-center justify-center rounded-full transition-transform duration-300 group-hover:scale-110">
              <Play className="tablet:h-9 tablet:w-9 text-olive-900 ml-1 h-12 w-12 fill-current" />
            </span>

            <div className="tablet:px-6 tablet:pb-6 absolute right-0 bottom-0 left-0 px-10 pb-8 text-right">
              <h3 className="tablet:text-[2rem] mb-2 text-[2.8rem] font-bold">
                {active.title}
              </h3>
              <p className="tablet:text-[1.5rem] tablet-sm:hidden max-w-3xl text-[1.8rem] text-gray-200">
                {active.description}
              </p>
            </div>
          </button>
        )}

        <span className="tablet:text-[1.3rem] bg-olive-900/80 absolute top-6 left-6 rounded-full px-4 py-1.5 text-[1.5rem] font-semibold text-gray-100 backdrop-blur-sm">
          {active.duration}
        </span>
      </div>

      {/* Playlist: absolutely positioned on desktop so the featured player drives the row height */}
      <div className="tablet:static relative">
        <ul className="tablet:static tablet:grid-cols-2 mobile-lg:grid-cols-1 absolute inset-0 grid auto-rows-min content-start gap-5 overflow-y-auto pl-3 [scrollbar-color:var(--color-olive-300)_transparent] [scrollbar-width:thin]">
          {videos.map((video) => {
            const isActive = video.id === active.id;

            return (
              <li key={video.id}>
                <button
                  type="button"
                  onClick={() => play(video)}
                  aria-current={isActive ? "true" : undefined}
                  className={cn(
                    "group hover:shadow-soft flex w-full cursor-pointer items-center gap-5 rounded-[0_3rem] border-2 bg-gray-100 p-3 text-right transition-all duration-300 hover:-translate-y-0.5",
                    isActive
                      ? "border-beige-500 shadow-soft"
                      : "border-transparent",
                  )}
                >
                  <span className="relative aspect-video w-40 shrink-0 overflow-hidden rounded-[0_2rem]">
                    <Image
                      src={video.poster}
                      alt={video.title}
                      fill
                      unoptimized
                      sizes="160px"
                      className="object-cover transition-transform duration-500 group-hover:scale-105"
                      draggable="false"
                    />
                    <span
                      className={cn(
                        "bg-olive-900/40 absolute inset-0 flex items-center justify-center transition-opacity",
                        isActive
                          ? "opacity-100"
                          : "opacity-0 group-hover:opacity-100",
                      )}
                    >
                      <Play className="h-7 w-7 fill-current text-gray-100" />
                    </span>
                  </span>

                  <span className="flex min-w-0 flex-1 flex-col gap-1">
                    <span
                      className={cn(
                        "truncate text-[1.7rem] font-bold",
                        isActive ? "text-beige-500" : "text-olive-500",
                      )}
                    >
                      {video.title}
                    </span>
                    <span className="line-clamp-2 text-[1.4rem] leading-snug text-gray-600">
                      {video.description}
                    </span>
                    <span className="text-[1.3rem] font-semibold text-gray-500">
                      {video.duration}
                    </span>
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
