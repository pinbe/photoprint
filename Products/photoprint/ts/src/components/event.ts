import {Format, Frame, Finish} from "./interfaces";

export const PHOTO_ORDER_OPTIONS_CHANGED_EVENT = 'PHOTO_ORDER_OPTIONS_CHANGED_EVENT';

export interface PhotoOrderOptionsChangedEventDetail {
    format: Format;
    finish: Finish;
    frame: Frame;
}
