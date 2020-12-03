import {Format, Frame} from "../photo_order";
export const PHOTO_ORDER_OPTIONS_CHANGED_EVENT = 'PHOTO_ORDER_OPTIONS_CHANGED_EVENT';


export interface PhotoOrderOptionsChangedEventDetail {
    format: Format;
    frame: Frame;

    // /**
    //  * Native image size in pixels
    //  */
    // fullSize: Size;
    // /**
    //  * top left corner of in situ frame, expressed in pixels
    //  */
    // tl: Point;
    // /**
    //  * bottom right corner of in situ frame
    //  */
    // br: Point;
    // /**
    //  * Real world frame width, delimited by top left and bottom right corners,
    //  * expressed in meters
    //  */
    // frameWidth: number;
    // /**
    //  * Foreground image size in real world, expressed in meters
    //  */
    // fgPaperSize: Size;
}
