import React, { useEffect, useState, useCallback } from "react";
import useEmblaCarousel from "embla-carousel-react";
import { result } from "../ResultScreens/data";
import "../ResultScreens/Industryresult.css";
import Model from '../ResultScreens/Model';

import Property from "./Property";

function Properties({ solutions }) {
    console.log("solutions",solutions);
    
    const [resultLen, setResultLen] = useState(0);
    const [emblaRef, emblaApi] = useEmblaCarousel({ loop: false, dragFree: true });

    useEffect(() => {
        setResultLen(solutions.length);
    }, [solutions]);

    const goToNext = useCallback(() => {
        if (emblaApi) emblaApi.scrollNext();
    }, [emblaApi]);

    const goToPrev = useCallback(() => {
        if (emblaApi) emblaApi.scrollPrev();
    }, [emblaApi]);

     const [isModalOpen, setIsModalOpen] = useState(false);
        const [modalData, setModalData] = useState([]);
        const [modalTitle, setModalTitle] = useState('');
    
        //Toggle modal on click of button
        const toggleModal = (data, title) => {
            setModalData(data);
            setModalTitle(title);
            setIsModalOpen(!isModalOpen);
        };

    return (
        <div className="reuslt-container flex flex-col w-full h-[98%] relative">
            {resultLen > 0 && (
                <div className="absolute top-2 right-2 flex space-x-2 z-10">
                    <button
                        className="embla__btn embla__prev px-3 py-1 bg-gray-800 text-white rounded"
                        onClick={goToPrev}
                        disabled={!emblaApi}
                    >
                        Prev
                    </button>
                    <button
                        className="embla__btn embla__next px-3 py-1 bg-gray-800 text-white rounded"
                        onClick={goToNext}
                        disabled={!emblaApi}
                    >
                        Next
                    </button>
                </div>
            )}

            <div className="solutions p-1 h-[95%]">
                <div className="embla h-full" ref={emblaRef}>
                    <div className="embla__container border-black h-full flex">
                        {solutions.map((solution, index) => (
                            <Property solution={solution} key={index} toggleModal={toggleModal} />
                        ))}
                    </div>
                </div>
            </div>
            <Model isOpen={isModalOpen} onClose={() => (setIsModalOpen(false))} title={modalTitle} data={modalData} />
        </div>
    );
}

export default Properties;
