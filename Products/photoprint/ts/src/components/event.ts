import {Format, Frame} from "./interfaces";

export const PHOTO_ORDER_OPTIONS_CHANGED_EVENT = 'PHOTO_ORDER_OPTIONS_CHANGED_EVENT';


export interface PhotoOrderOptionsChangedEventDetail {
    format: Format;
    frame: Frame;
}
