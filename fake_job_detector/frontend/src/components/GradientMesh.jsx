import React, { useEffect, useRef } from 'react';

export default function GradientMesh() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId;
    let time = 0;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize, { passive: true });

    // Ambient Mesh orbs — orange + rose + amber
    const orbs = [
      { x: 0.15, y: 0.25, r: 0.38, color: 'rgba(249, 115, 22, 0.08)', speed: 0.0007 },
      { x: 0.85, y: 0.20, r: 0.35, color: 'rgba(244, 63, 94, 0.07)', speed: 0.0011 },
      { x: 0.50, y: 0.75, r: 0.42, color: 'rgba(251, 146, 60, 0.06)', speed: 0.0005 },
      { x: 0.10, y: 0.80, r: 0.30, color: 'rgba(244, 63, 94, 0.05)', speed: 0.0009 },
      { x: 0.90, y: 0.70, r: 0.36, color: 'rgba(249, 115, 22, 0.07)', speed: 0.0008 },
    ];

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      time++;

      orbs.forEach((orb, i) => {
        const x = (orb.x + Math.sin(time * orb.speed + i * 1.5) * 0.12) * canvas.width;
        const y = (orb.y + Math.cos(time * orb.speed * 0.8 + i * 1.2) * 0.10) * canvas.height;
        const r = orb.r * Math.max(canvas.width, canvas.height);

        const grad = ctx.createRadialGradient(x, y, 0, x, y, r);
        grad.addColorStop(0, orb.color);
        grad.addColorStop(1, 'transparent');

        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(x, y, r, 0, Math.PI * 2);
        ctx.fill();
      });

      animId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', resize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className="fixed inset-0 z-0 pointer-events-none"
      style={{ opacity: 1 }}
    />
  );
}
