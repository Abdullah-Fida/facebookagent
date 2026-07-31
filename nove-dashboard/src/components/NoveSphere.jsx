import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

/* ═══════════════════════════════════════════════════════════════
   Particle Sphere — Thousands of tiny white dots on sphere surface
   Black & white aesthetic matching the reference image
   ═══════════════════════════════════════════════════════════════ */

export function ChatGPTOrb({ aiState, targetX, targetY, targetScale }) {
  const groupRef = useRef();
  const innerRef = useRef();
  const outerRef = useRef();
  const glowRef = useRef();

  const smoothRef = useRef({
    x: 0, y: 0, scale: 1,
    intensity: 0,
  });

  // --- Inner sphere: dense dots on the surface ---
  const innerGeom = useMemo(() => {
    const geom = new THREE.BufferGeometry();
    const count = 6000;
    const positions = new Float32Array(count * 3);
    const sizes = new Float32Array(count);

    for (let i = 0; i < count; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos((Math.random() * 2) - 1);
      const r = 2.0 + (Math.random() - 0.5) * 0.08; // Tight to sphere surface

      positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = r * Math.cos(phi);
      sizes[i] = 0.008 + Math.random() * 0.025;
    }

    geom.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geom.setAttribute('aSize', new THREE.BufferAttribute(sizes, 1));
    return { geom, origPositions: positions.slice() };
  }, []);

  // --- Outer halo: sparse larger dots ---
  const outerGeom = useMemo(() => {
    const geom = new THREE.BufferGeometry();
    const count = 1200;
    const positions = new Float32Array(count * 3);

    for (let i = 0; i < count; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos((Math.random() * 2) - 1);
      const r = 2.1 + Math.random() * 0.6;

      positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = r * Math.cos(phi);
    }

    geom.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    return geom;
  }, []);

  // --- Soft glow ring ---
  const glowGeom = useMemo(() => {
    const geom = new THREE.BufferGeometry();
    const count = 400;
    const positions = new Float32Array(count * 3);

    for (let i = 0; i < count; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos((Math.random() * 2) - 1);
      const r = 2.6 + Math.random() * 0.5;

      positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = r * Math.cos(phi);
    }

    geom.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    return geom;
  }, []);

  useFrame((state) => {
    const t = state.clock.getElapsedTime();
    const sm = smoothRef.current;

    // Smooth intensity
    let targetIntensity = 0;
    if (aiState === 'listening') targetIntensity = 0.3;
    else if (aiState === 'thinking') targetIntensity = 0.6;
    else if (aiState === 'speaking') targetIntensity = 1.0;
    sm.intensity += (targetIntensity - sm.intensity) * 0.06;

    // --- Animate inner particles ---
    if (innerRef.current) {
      const pos = innerGeom.geom.attributes.position;
      const orig = innerGeom.origPositions;

      for (let i = 0; i < pos.count; i++) {
        const ox = orig[i * 3];
        const oy = orig[i * 3 + 1];
        const oz = orig[i * 3 + 2];

        const len = Math.sqrt(ox * ox + oy * oy + oz * oz);
        const nx = ox / len, ny = oy / len, nz = oz / len;

        // Slow organic flow
        const flow = (Math.sin(t * 0.4 + ox * 2.0 + oy) + Math.cos(t * 0.35 + oz * 1.8)) * 0.015;

        // Speaking vibration
        const vib = aiState === 'speaking'
          ? sm.intensity * Math.sin(t * 25 + i * 0.5) * 0.04
          : 0;

        // Thinking pulse
        const pulse = aiState === 'thinking'
          ? Math.sin(t * 2.5 + i * 0.2) * 0.02 * sm.intensity
          : 0;

        const d = flow + vib + pulse;
        pos.setXYZ(i, ox + nx * d, oy + ny * d, oz + nz * d);
      }
      pos.needsUpdate = true;

      // Opacity based on state
      innerRef.current.material.opacity = 0.7 + sm.intensity * 0.3;
    }

    // --- Outer halo opacity ---
    if (outerRef.current) {
      outerRef.current.material.opacity = 0.15 + sm.intensity * 0.2;
    }

    // --- Glow ---
    if (glowRef.current) {
      glowRef.current.material.opacity = 0.05 + sm.intensity * 0.12;
    }

    // --- Smooth position, scale, rotation ---
    if (groupRef.current) {
      const tx = targetX || 0;
      const ty = targetY || 0;
      const ts = targetScale || 1;

      sm.x += (tx - sm.x) * 0.035;
      sm.y += (ty - sm.y) * 0.035;
      sm.scale += (ts - sm.scale) * 0.035;

      groupRef.current.position.x = sm.x;
      groupRef.current.position.y = sm.y;

      const pulse = aiState === 'speaking' ? sm.intensity * 0.02 * Math.sin(t * 10) : 0;
      const s = sm.scale + pulse;
      groupRef.current.scale.set(s, s, s);

      // Slow rotation
      groupRef.current.rotation.y = t * 0.03;
      groupRef.current.rotation.x = Math.sin(t * 0.015) * 0.1;
    }
  });

  return (
    <group ref={groupRef}>
      {/* Dense surface particles */}
      <points ref={innerRef} geometry={innerGeom.geom}>
        <pointsMaterial
          size={0.02}
          color="#ffffff"
          transparent
          opacity={0.75}
          sizeAttenuation
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </points>

      {/* Sparse outer halo */}
      <points ref={outerRef} geometry={outerGeom}>
        <pointsMaterial
          size={0.015}
          color="#ffffff"
          transparent
          opacity={0.2}
          sizeAttenuation
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </points>

      {/* Soft distant glow */}
      <points ref={glowRef} geometry={glowGeom}>
        <pointsMaterial
          size={0.04}
          color="#aaaaaa"
          transparent
          opacity={0.08}
          sizeAttenuation
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </points>
    </group>
  );
}

export default ChatGPTOrb;