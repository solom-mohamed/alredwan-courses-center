"use client";

import { MemoryListItem } from "@/types/entities";
import { getFullImageUrl } from "@/lib/image-utils";
import { useEffect } from "react";
import Image from "next/image";
import Button from "@/components/ui/Button";
import { deleteMemory } from "@/actions/memories";
import toast from "react-hot-toast";
import { useState } from "react";
import ConfirmationModal from "@/components/ui/ConfirmationModal";

interface Props {
  memories: MemoryListItem[];
  initialIndex: number;
  onClose: () => void;
  onMemoryDeleted: (id: string) => void;
  isSupervisor: boolean;
}

export default function Lightbox({ memories, initialIndex, onClose, onMemoryDeleted, isSupervisor }: Props) {
  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  
  const memory = memories[currentIndex];
  
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowRight") setCurrentIndex(i => Math.min(i + 1, memories.length - 1));
      if (e.key === "ArrowLeft") setCurrentIndex(i => Math.max(i - 1, 0));
    };
    window.addEventListener("keydown", handleKeyDown);
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "auto";
    };
  }, [onClose, memories.length]);

  if (!memory) return null;

  const url = getFullImageUrl(memory.file_url) || "";

  const handleDelete = async () => {
    setIsDeleting(true);
    const result = await deleteMemory(memory.id);
    setIsDeleting(false);
    setShowDeleteConfirm(false);
    if (result.ok) {
      toast.success(result.message || "تم الحذف بنجاح");
      onMemoryDeleted(memory.id);
    } else {
      toast.error(result.message || "فشل الحذف");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm">
      <div className="absolute top-4 right-4 flex gap-4">
        {isSupervisor && (
          <Button variant="secondary" className="bg-red-500 hover:bg-red-600 text-white border-red-500" onClick={() => setShowDeleteConfirm(true)}>
            حذف الذكرى
          </Button>
        )}
        <button onClick={onClose} className="text-white hover:text-gray-300">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M18 6L6 18M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="absolute left-4 top-1/2 -translate-y-1/2">
        <button 
          onClick={() => setCurrentIndex(i => Math.min(i + 1, memories.length - 1))}
          className={`p-2 text-white hover:text-gray-300 ${currentIndex === memories.length - 1 ? 'opacity-30 cursor-not-allowed' : ''}`}
          disabled={currentIndex === memories.length - 1}
        >
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M9 18l6-6-6-6" />
          </svg>
        </button>
      </div>

      <div className="absolute right-4 top-1/2 -translate-y-1/2">
        <button 
          onClick={() => setCurrentIndex(i => Math.max(i - 1, 0))}
          className={`p-2 text-white hover:text-gray-300 ${currentIndex === 0 ? 'opacity-30 cursor-not-allowed' : ''}`}
          disabled={currentIndex === 0}
        >
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M15 18l-6-6 6-6" />
          </svg>
        </button>
      </div>

      <div className="max-h-[90vh] max-w-[90vw] flex flex-col items-center">
        {memory.media_type === "image" ? (
          <div className="relative h-[70vh] w-[80vw]">
            <Image src={url} alt={memory.caption} fill className="object-contain" />
          </div>
        ) : (
          <video src={url} controls className="max-h-[70vh] max-w-[80vw]" autoPlay />
        )}
        
        <div className="mt-6 text-center text-white max-w-2xl">
          {memory.caption && <p className="text-lg mb-2">{memory.caption}</p>}
          <div className="text-sm text-gray-400">
            تم الرفع بواسطة {memory.uploader_name}
          </div>
          {memory.tagged_participants.length > 0 && (
            <div className="mt-3 flex flex-wrap justify-center gap-2">
              {memory.tagged_participants.map(p => (
                <span key={p.id} className="bg-white/10 px-3 py-1 rounded-full text-xs">
                  {p.name}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
      
      <ConfirmationModal
        isOpen={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        onConfirm={handleDelete}
        title="حذف الذكرى"
        description="هل أنت متأكد من حذف هذه الذكرى؟ لا يمكن التراجع عن هذا الإجراء."
        confirmText="حذف"
        cancelText="إلغاء"
        variant="danger"
      />
    </div>
  );
}
