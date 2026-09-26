import { getLandingVideos } from "@/actions/landing";
import VideoReel from "@/components/landing-page/VideoReel";
import ScrollReveal from "@/components/ui/ScrollReveal";

/** "شاهد الواحة عن قرب": the reel of short clips managed from the admin. Hidden when there are none. */
export default async function VideosSection() {
  const videos = await getLandingVideos();
  if (videos.length === 0) return null;

  return (
    <section
      id="videos"
      className="mobile-lg:px-6! flex flex-col items-center bg-[linear-gradient(180deg,#FFF_0%,#EEF2EC_100%)] px-16!"
    >
      <ScrollReveal
        direction="up"
        className="flex w-full flex-col items-center"
      >
        <div className="title-block">
          <h2>
            شاهد <span>الواحة</span> عن قرب
          </h2>
          <p className="mb-24 max-w-200 text-center text-4xl text-gray-600">
            مقاطع قصيرة من داخل واحة الرضوان تنقل لك أجواء التعلم والأنشطة وقصص
            طلابنا
          </p>
        </div>
      </ScrollReveal>

      <ScrollReveal
        direction="up"
        delay={0.2}
        amount={0.1}
        className="flex w-full flex-col items-center"
      >
        <VideoReel videos={videos} />
      </ScrollReveal>
    </section>
  );
}
