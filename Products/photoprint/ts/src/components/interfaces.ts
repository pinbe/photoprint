type RefPrice = { reference: string, price: number };
interface IPrintOfferItem {
    reference: string;
    label: string;
}

export interface Format extends IPrintOfferItem {
    short_edge: number;
    long_edge: number;
    price: number;
    available_copies: number | boolean;
}

export interface Finish extends IPrintOfferItem {
    description: string;
    formats_prices: RefPrice[];
}

export interface FrameBorderDescription {
    url: string;
    real_width: number;
    background: string;
}

export interface Frame extends IPrintOfferItem {
    description: string;
    finishes: string[];
    frame_border_description?: FrameBorderDescription;
    formats_prices: RefPrice[];
}

export interface PrintInfos {
    formats: Format[];
    finishes: Finish[];
    frames: Frame[];
}

export interface SelectedOptions {
    format?: string;
    finish?: string;
    frame?: string;
}
