import React, { useEffect, useState } from 'react';
import { motion, useMotionValue, useSpring } from 'framer-motion';

export default function CustomCursor() {
  const cursorX = useMotionValue(-100);
  const cursorY = useMotionValue(-100);
  const trailX = useMotionValue(-100);
  const trailY = useMotionValue(-100);

  const springX = useSpring(cursorX, { stiffness: 800, damping: 40 });
  const springY = useSpring(cursorY, { stiffness: 800, damping: 40 });
  const trailSpringX = useSpring(trailX, { stiffness: 150, damping: 20 });
  const trailSpringY = useSpring(trailY, { stiffness: 150, damping: 20 });

  const [isHovering, setIsHovering] = useState(false);
  const [isMagnetic, setIsMagnetic] = useState(false);
  const [clicked, setClicked] = useState(false);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Only enable on desktop pointer devices
    if (typeof window === 'undefined' || !window.matchMedia('(pointer: fine)').matches) {
      return;
    }

    const moveCursor = (e) => {
      if (!isVisible) setIsVisible(true);
      cursorX.set(e.clientX - 8);
      cursorY.set(e.clientY - 8);
      trailX.set(e.clientX - 20);
      trailY.set(e.clientY - 20);
    };

    const handleMouseDown = () => setClicked(true);
    const handleMouseUp = () => setClicked(false);
    const handleMouseLeave = () => setIsVisible(false);
    const handleMouseEnter = () => setIsVisible(true);

    const handleInteractiveEnter = () => setIsHovering(true);
    const handleInteractiveLeave = () => setIsHovering(false);

    const handleMagneticEnter = () => setIsMagnetic(true);
    const handleMagneticLeave = () => setIsMagnetic(false);

    const attachListeners = () => {
      const interactives = document.querySelectorAll('button, a, input, textarea, select, .card-hover, [role="button"]');
      interactives.forEach(el => {
        el.addEventListener('mouseenter', handleInteractiveEnter);
        el.addEventListener('mouseleave', handleInteractiveLeave);
      });

      const magnetics = document.querySelectorAll('button, a, .magnetic');
      magnetics.forEach(btn => {
        btn.addEventListener('mouseenter', handleMagneticEnter);
        btn.addEventListener('mouseleave', handleMagneticLeave);
      });
    };

    attachListeners();
    const interval = setInterval(attachListeners, 2000);

    window.addEventListener('mousemove', moveCursor, { passive: true });
    window.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mouseup', handleMouseUp);
    document.addEventListener('mouseleave', handleMouseLeave);
    document.addEventListener('mouseenter', handleMouseEnter);

    return () => {
      clearInterval(interval);
      window.removeEventListener('mousemove', moveCursor);
      window.removeEventListener('mousedown', handleMouseDown);
      window.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('mouseleave', handleMouseLeave);
      document.removeEventListener('mouseenter', handleMouseEnter);
    };
  }, [isVisible]);

  return (
    <>
      {/* Spotlight subtle glow following cursor */}
      <motion.div
        aria-hidden="true"
        className="fixed top-0 left-0 w-72 h-72 z-0 pointer-events-none rounded-full"
        style={{
          x: trailSpringX,
          y: trailSpringY,
          marginLeft: '-128px',
          marginTop: '-128px',
          background: 'radial-gradient(circle, rgba(249,115,22,0.07) 0%, rgba(244,63,94,0.03) 45%, transparent 70%)',
          filter: 'blur(24px)',
          opacity: isVisible ? 1 : 0,
          willChange: 'transform'
        }}
      />

      {/* Trail ring */}
      <motion.div
        aria-hidden="true"
        animate={{
          scale: isMagnetic ? 2.2 : isHovering ? 1.5 : 1,
          opacity: isVisible ? (isMagnetic ? 0.7 : 0.35) : 0,
          rotate: isMagnetic ? 45 : 0
        }}
        transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
        className="fixed top-0 left-0 w-10 h-10 rounded-full z-[9998] pointer-events-none border-2"
        style={{
          x: trailSpringX,
          y: trailSpringY,
          borderColor: '#F97316',
          boxShadow: '0 0 15px rgba(249,115,22,0.35)',
          willChange: 'transform'
        }}
      />

      {/* Main cursor dot */}
      <motion.div
        aria-hidden="true"
        animate={{
          scale: clicked ? 0.7 : isHovering ? 1.6 : 1,
          opacity: isVisible ? 1 : 0
        }}
        transition={{ duration: 0.12 }}
        className="fixed top-0 left-0 w-4 h-4 rounded-full z-[9999] pointer-events-none"
        style={{
          x: springX,
          y: springY,
          background: 'linear-gradient(135deg, #F97316 0%, #F43F5E 100%)',
          boxShadow: isHovering
            ? '0 0 20px rgba(249,115,22,0.8), 0 0 35px rgba(244,63,94,0.45)'
            : '0 0 10px rgba(249,115,22,0.5)',
          willChange: 'transform'
        }}
      />
    </>
  );
}
