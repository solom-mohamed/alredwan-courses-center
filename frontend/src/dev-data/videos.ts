import Poster1 from "@/assets/image-grid/image-1.webp";
import Poster3 from "@/assets/image-grid/image-3.webp";
import Poster4 from "@/assets/image-grid/image-4.webp";
import Poster6 from "@/assets/image-grid/image-6.webp";
import Poster8 from "@/assets/image-grid/image-8.webp";

export interface LandingVideo {
  id: number;
  title: string;
  description: string;
  /** Display-only duration label, e.g. "1:20" */
  duration: string;
  /** Direct MP4 URL (Cloudinary or any public host) */
  src: string;
  /** Poster image shown before playback */
  poster: string;
}

/**
 * Static placeholder videos for the landing page.
 * Replace `src` / `poster` with the real clips (1–2 minutes each) when ready.
 */
export const landingVideos: LandingVideo[] = [
  {
    id: 1,
    title: "جولة داخل واحة الرضوان",
    description: "نظرة سريعة على قاعاتنا وأجواء التعلم اليومية في الواحة.",
    duration: "1:45",
    src: "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/Big_Buck_Bunny_360_10s_1MB.mp4",
    poster: Poster1.src,
  },
  {
    id: 2,
    title: "حلقات تحفيظ القرآن الكريم",
    description: "لقطات من حلقات الحفظ والتلاوة مع معلمينا المجازين.",
    duration: "1:20",
    src: "https://mdn.github.io/shared-assets/videos/flower.mp4",
    poster: Poster3.src,
  },
  {
    id: 3,
    title: "أنشطتنا الترفيهية والرحلات",
    description:
      "الأنشطة الجماعية والرحلات التي تبني شخصية الطفل وتقوي روابطه.",
    duration: "2:00",
    src: "https://test-videos.co.uk/vids/sintel/mp4/h264/360/Sintel_360_10s_1MB.mp4",
    poster: Poster4.src,
  },
  {
    id: 4,
    title: "كلمة أولياء الأمور",
    description: "آراء أولياء الأمور وتجاربهم مع أبنائهم في الواحة.",
    duration: "1:30",
    src: "https://test-videos.co.uk/vids/jellyfish/mp4/h264/360/Jellyfish_360_10s_1MB.mp4",
    poster: Poster6.src,
  },
  {
    id: 5,
    title: "حفل تكريم الحفظة",
    description: "لحظات من حفل تكريم طلابنا المتميزين وختم القرآن الكريم.",
    duration: "1:55",
    src: "https://www.w3schools.com/html/mov_bbb.mp4",
    poster: Poster8.src,
  },
];
