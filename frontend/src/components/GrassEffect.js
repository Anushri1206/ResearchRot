import React, { useRef, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Box, IconButton, Fade } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import GrassIcon from '@mui/icons-material/Grass';

const GrassBlade = ({ position, mousePosition }) => {
  const meshRef = useRef();
  const [hovered, setHovered] = useState(false);

  useFrame((state) => {
    if (meshRef.current) {
      const distance = Math.sqrt(
        Math.pow(mousePosition.x - position[0], 2) +
        Math.pow(mousePosition.y - position[1], 2)
      );
      
      const maxDistance = 2;
      const bendAmount = Math.max(0, 1 - distance / maxDistance);
      
      meshRef.current.rotation.z = Math.sin(state.clock.elapsedTime * 2) * 0.1 * bendAmount;
    }
  });

  return (
    <mesh
      ref={meshRef}
      position={position}
      onPointerOver={() => setHovered(true)}
      onPointerOut={() => setHovered(false)}
    >
      <planeGeometry args={[0.1, 1, 1]} />
      <meshStandardMaterial color={hovered ?   '#8BC34A':'rgba(126, 252, 0, 0.52)'} />
    </mesh>
  );
};

const GrassField = ({ mousePosition }) => {
  const grassBlades = [];
  const gridSize = 20;
  const spacing = 0.2;

  for (let x = -gridSize/2; x < gridSize/2; x++) {
    for (let z = -gridSize/2; z < gridSize/2; z++) {
      grassBlades.push(
        <GrassBlade
          key={`${x}-${z}`}
          position={[x * spacing, 0, z * spacing]}
          mousePosition={mousePosition}
        />
      );
    }
  }

  return <>{grassBlades}</>;
};

const GrassEffect = ({ onClose }) => {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [showGrass, setShowGrass] = useState(false);

  const handleMouseMove = (event) => {
    const { clientX, clientY } = event;
    const x = (clientX / window.innerWidth) * 2 - 1;
    const y = -(clientY / window.innerHeight) * 2 + 1;
    setMousePosition({ x, y });
  };

  return (
    <Box
      sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        zIndex: 1000,
        bgcolor: 'rgba(0, 0, 0, 0.8)',
      }}
      onMouseMove={handleMouseMove}
    >
      <IconButton
        onClick={onClose}
        sx={{
          position: 'absolute',
          top: 16,
          right: 16,
          color: 'white',
          zIndex: 1001,
        }}
      >
        <CloseIcon />
      </IconButton>
      <Canvas camera={{ position: [0, 3, 6], fov: 55 }}>
                <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} />
        <GrassField mousePosition={mousePosition} />
      </Canvas>
    </Box>
  );
};

export default GrassEffect; 