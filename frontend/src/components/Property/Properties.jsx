import React, { useEffect, useState } from 'react'
import useEmblaCarousel from 'embla-carousel-react'
import { result } from '../ResultScreens/data'
import '../ResultScreens/Industryresult.css'

import Property from './Property';

// function Industryresult({ result }) {
function Properties({ solutions }) {
    // function Industryresult() {
    console.log("result in indeustry solution screen", result);
    const analytics_response = result["Analytics_response"]
    console.log("Analytics_response", analytics_response);

    const [resultLen, setResultLen] = useState(0)
    // const [solutions, setSolutions] = useState([])
    const [emblaRef, emblaApi] = useEmblaCarousel({ dragFree: true, watchDrag: false });


    // Update the resultLen after the solutions are fetched
    useEffect(() => {
        setResultLen(solutions.length);
        console.log("final solutions2", solutions);
    }, [solutions])

    const goToNext = () => {
        if (emblaApi) {
            emblaApi.scrollNext();
        }
    };

    const goToPrev = () => {
        if (emblaApi) {
            emblaApi.scrollPrev();
        }
    };
    useEffect(() => {
        if (emblaApi) {
            emblaApi.on('select', () => {
                document.querySelectorAll('.embla__slide').forEach(slide => {
                    slide.style.backgroundColor = 'rgb(135 197 235 / 41%)';
                });
            });
        }
    }, [emblaApi]);

    return (
        <div className="reuslt-container flex flex-col w-full h-[93%] relative">
            {/* Navigation Buttons Positioned at Top-Right */}
            {resultLen > 0 && (
                <div className="absolute top-2 right-2 flex space-x-2">
                    <button className="embla__btn embla__prev px-3 py-1 bg-gray-800 text-white rounded" onClick={goToPrev}>Prev</button>
                    <button className="embla__btn embla__next px-3 py-1 bg-gray-800 text-white rounded" onClick={goToNext}>Next</button>
                </div>
            )}

            <div className="solutions p-1 h-[95%]">
                <div className="embla h-full" ref={emblaRef}>
                    <div className="embla__container border-black h-full">
                        {solutions.map((solution, index) => (
                            <Property solution={solution} key={index} />
                        ))}
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Properties