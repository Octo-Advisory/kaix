import React, { useEffect, useRef, useState } from 'react';
import { Swiper, SwiperSlide } from 'swiper/react';
import { EffectFade, Mousewheel } from 'swiper/modules';
import gsap from 'gsap';
import 'swiper/css';
import 'swiper/css/effect-fade';
import image1 from '../../assets/Images/1.1.0-scaled.jpg';
import image2 from '../../assets/Images/7.0-scaled.jpg';
import image3 from '../../assets/Images/IMG_8763.JPG';
import Navbar from '../Navbar/Navbar';

export default function ScrollSyncedSwiperSection() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const swiperRef = useRef(null);
  const sectionRef = useRef(null);
  const images = [image1, image2, image3];
  const animationRef = useRef(null);

  // Initialize animations
  useEffect(() => {
    // Text animation
    gsap.from(".title-text", {
      y: 40,
      opacity: 0,
      duration: 1.8,
      ease: "elastic.out(1, 0.5)",
      delay: 0.4
    });

    // Clean up animations on unmount
    return () => {
      if (animationRef.current) {
        animationRef.current.kill();
      }
    };
  }, []);

  // Enhanced scroll handling
  useEffect(() => {
    const section = sectionRef.current;
    if (!section) return;

    let isAnimating = false;
    let scrollTimeout;

    const handleScroll = (e) => {
      e.preventDefault();
      
      if (isAnimating || !swiperRef.current?.swiper) return;
      isAnimating = true;

      const delta = e.deltaY;
      const swiper = swiperRef.current.swiper;
      const direction = delta > 0 ? 1 : -1;

      if (animationRef.current) {
        animationRef.current.kill();
      }

      animationRef.current = gsap.to(swiper, {
        progress: swiper.progress + (0.0005 * direction),
        duration: 2.5,
        ease: "sine.inOut",
        onUpdate: () => {
          if (direction > 0) swiper.slideNext();
          else swiper.slidePrev();
        },
        onComplete: () => {
          clearTimeout(scrollTimeout);
          scrollTimeout = setTimeout(() => isAnimating = false, 300);
        }
      });
    };

    section.addEventListener('wheel', handleScroll, { passive: false });
    return () => {
      section.removeEventListener('wheel', handleScroll);
      clearTimeout(scrollTimeout);
    };
  }, []);

  const handleSlideChange = (swiper) => {
    setCurrentIndex(swiper.realIndex);
    
    // Safely animate the active slide image
    const activeSlideImg = document.querySelector('.swiper-slide-active img');
    if (activeSlideImg) {
      gsap.killTweensOf(activeSlideImg);
      gsap.fromTo(activeSlideImg,
        { scale: 0.95, opacity: 0.8 },
        {
          scale: 1.05,
          opacity: 1,
          duration: 2.5,
          ease: "power2.inOut"
        }
      );
    }
  };

  return (
    <>
      <Navbar />
      <div className='absolute z-50 font-semibold text-lg top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full flex flex-row justify-between px-6'>
        <h1 className='select-none'>SCROLL</h1>
        <h1 className='select-none'>{currentIndex + 1} - {images.length}</h1>
      </div>
      <section
        ref={sectionRef}
        className="h-screen w-screen flex items-center justify-center bg-[#d9d9d9] overflow-hidden"
      >
        <div 
          className="h-[65vh] w-[70vw] rounded-2xl overflow-hidden shadow-2xl relative"
          style={{ perspective: '1200px' }}
        >
          <h1 className="title-text absolute z-50 font-bold text-9xl text-white/90 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 mix-blend-overlay tracking-tighter">
            GRAPITS
          </h1>
          
          <Swiper
            ref={swiperRef}
            direction="vertical"
            onSlideChange={handleSlideChange}
            slidesPerView={1}
            loop={true}
            effect="fade"
            fadeEffect={{
              crossFade: true,
              duration: 2800
            }}
            speed={2800}
            modules={[EffectFade, Mousewheel]}
            mousewheel={false}
            className="h-full w-full"
            onInit={(swiper) => {
              // Initialize first slide animation
              const firstSlideImg = swiper.slides[0]?.querySelector('img');
              if (firstSlideImg) {
                gsap.set(firstSlideImg, { scale: 1.05 });
              }
            }}
          >
            {images.map((img, index) => (
              <SwiperSlide 
                key={index}
                className="relative"
                style={{
                  backfaceVisibility: 'hidden',
                  transformStyle: 'preserve-3d'
                }}
              >
                <div className="absolute inset-0 bg-black/20"></div>
                <img
                  src={img}
                  alt=""
                  className="absolute h-full w-full object-cover transform transition-all duration-[1500ms] ease-[cubic-bezier(0.22,1,0.36,1)]"
                  style={{
                    backfaceVisibility: 'hidden',
                    willChange: 'transform, opacity'
                  }}
                  loading="eager"
                />
              </SwiperSlide>
            ))}
          </Swiper>
          
          <div className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent pointer-events-none"></div>
        </div>
      </section>
    </>
  );
}