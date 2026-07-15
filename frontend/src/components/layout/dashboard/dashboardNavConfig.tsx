import AllCoursesIcon from "@/components/icons/AllCoursesIcon";
import ClipboardIcon from "@/components/icons/ClipboardIcon";
import MyCoursesIcon from "@/components/icons/MyCoursesIcon";
import OverviewIcon from "@/components/icons/OverviewIcon";
import PanelsIcon from "@/components/icons/PanelsIcon";
import PeopleIcon from "@/components/icons/PeopleIcon";
import PersonIcon from "@/components/icons/PersonIcon";
import MosqueIcon from "@/components/icons/MosqueIcon";
import { UserEntity } from "@/types/auth";
import { ReactNode } from "react";

export interface DashboardNavItem {
  label: string;
  href: string;
  icon?: ReactNode;
  nestedNavLinks?: {
    href: string;
    label: string;
  }[];
  className?: string;
}

const roleMap: Record<UserEntity["role"], DashboardNavItem[]> = {
  admin: [
    {
      label: "حضور اليوم",
      href: "/dashboard/todays-staff-attendances",
      icon: <ClipboardIcon />,
    },
    {
      label: "جميع الحضور",
      href: "/dashboard/all-attendances",
      icon: <OverviewIcon />,
    },
    {
      label: "المعلمون",
      href: "/dashboard/instructors",
      icon: <PeopleIcon />,
    },
    {
      label: "الجداول",
      href: "/dashboard/season-schedules",
      icon: <PanelsIcon />,
    },
    {
      label: "جميع الدورات",
      href: "/dashboard/courses",
      icon: <AllCoursesIcon />,
    },
    {
      label: "ذكريات المسجد",
      href: "/dashboard/memories",
      icon: <MosqueIcon />,
    },
  ],

  supervisor: [
    {
      label: "حضور اليوم",
      href: "/dashboard/todays-staff-attendances",
      icon: <ClipboardIcon />,
    },
    {
      label: "جميع الحضور",
      href: "/dashboard/all-attendances",
      icon: <OverviewIcon />,
    },
    {
      label: "المعلمون",
      href: "/dashboard/instructors",
      icon: <PeopleIcon />,
    },
    {
      label: "ذكريات المسجد",
      href: "/dashboard/memories",
      icon: <MosqueIcon />,
    },
  ],

  instructor: [
    {
      label: "محاضرات اليوم",
      href: "/dashboard/todays-schedule",
      icon: <PanelsIcon />,
    },
    {
      label: "جميع الدورات",
      href: "/dashboard/my-courses",
      icon: <ClipboardIcon />,
      nestedNavLinks: [
        {
          href: "lectures",
          label: "المحاضرات",
        },
        {
          href: "",
          label: "تفاصيل الدورة",
        },
        {
          href: "enrollments",
          label: "الحجوزات",
        },
      ],
    },
    {
      label: "ذكريات المسجد",
      href: "/dashboard/memories",
      icon: <MosqueIcon />,
    },
    {
      label: "الملف الشخصي",
      href: "/dashboard/profile",
      icon: <PersonIcon />,
      className: "mb-auto",
    },
  ],

  parent: [
    {
      label: "نظرة عامة",
      href: "/dashboard/overview",
      icon: <OverviewIcon />,
    },
    {
      label: "أطفالي",
      href: "/dashboard/my-children",
      icon: <PeopleIcon />,
      nestedNavLinks: [
        {
          href: "",
          label: "نظرة عامة",
        },
        {
          label: "الدورات",
          href: "courses",
        },
        {
          label: "الملف الشخصي",
          href: "profile",
        },
      ],
    },
    {
      label: "جميع الدورات",
      href: "/dashboard/courses",
      icon: <AllCoursesIcon />,
    },
    {
      label: "ذكريات المسجد",
      href: "/dashboard/memories",
      icon: <MosqueIcon />,
    },
    {
      label: "الملف الشخصي",
      href: "/dashboard/profile",
      icon: <PersonIcon />,
      className: "mb-auto",
    },
  ],

  student: [
    {
      label: "نظرة عامة",
      href: "/dashboard/overview",
      icon: <OverviewIcon />,
    },
    {
      label: "دوراتي",
      href: "/dashboard/my-courses",
      icon: <MyCoursesIcon />,
      nestedNavLinks: [
        {
          href: "lectures",
          label: "المحاضرات",
        },
        {
          href: "",
          label: "تفاصيل الدورة",
        },
        {
          href: "enrollments",
          label: "الحجوزات",
        },
      ],
    },
    {
      label: "جميع الدورات",
      href: "/dashboard/courses",
      icon: <AllCoursesIcon />,
    },
    {
      label: "ذكريات المسجد",
      href: "/dashboard/memories",
      icon: <MosqueIcon />,
    },
    {
      label: "الملف الشخصي",
      href: "/dashboard/profile",
      icon: <PersonIcon />,
      className: "mb-auto",
    },
  ],
};

export function getDashboardNavItems(role: UserEntity["role"]) {
  return roleMap[role];
}

