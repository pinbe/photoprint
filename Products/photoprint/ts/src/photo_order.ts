import * as d3 from "d3";
import i18next, {TOptions} from "i18next";
import HttpApi from "i18next-http-backend";
import LanguageDetector from "i18next-browser-languagedetector";

const _ = (s: string, options?: TOptions): string => i18next.t(s, options);

type RefPrice = { reference: string, price: number };

interface IPrintOfferItem {
    reference: string;
    label: string;
}

interface Format extends IPrintOfferItem {
    short_edge: number;
    long_edge: number;
    price: number;
}

interface Finish extends IPrintOfferItem {
    description: string;
    formats_prices: RefPrice[];
}

interface Frame extends IPrintOfferItem{
    description: string;
    finishes: string[];
    formats_prices: RefPrice[];
}

interface PrintInfos {
    formats: Format[];
    finishes: Finish[];
    frames: Frame[];
}

interface SelectedOptions {
    format?: string;
    finish?: string;
    frame?: string;
}

class PhotoOrder {
    private readonly uid: string;
    private readonly portal_url: string;
    private readonly wrapper: HTMLElement;
    private printInfos: PrintInfos;
    private static FORMATS_CHOICES_CLS = 'formats'
    private static FINISHES_CHOICES_CLS = 'finishes'
    private static FRAMES_CHOICES_CLS = 'frames'
    private selectedOptions: SelectedOptions;

    constructor(portal_url: string,
                uid: string,
                wrapper: HTMLElement) {
        this.uid = uid;
        this.portal_url = portal_url;
        this.wrapper = wrapper;
        this.printInfos = null;
        this.selectedOptions = {};

        const params = new FormData();
        params.append('cmf_uid', this.uid)
        d3.json(
            `${this.portal_url}/portal_photo_print/getEffectivePrintingOptionsFor`,
            {
                method: 'POST',
                body: params
            })
            .then((value: PrintInfos) => {
                this.printInfos = value;
                this.draw();
            });
    }

    draw() {
        /** Formats */
        const form = d3.select(this.wrapper)
            .append('form')
            .attr('action', '#')
            .on('change', () => this.onFormChange(d3.event))
        ;
        form
            .append('div')
            .attr('class', 'section-option-label')
            .text(_('Format'))
        ;
        form
            .append('div')
            .attr('class', `choices ${PhotoOrder.FORMATS_CHOICES_CLS}`)
            .selectAll('div')
            .data(this.printInfos.formats)
            .enter()
            .append('div')
            .html(
                (d: Format) =>
                    `
                <span>
                  <label>
                    <input type="radio" name="format" value="${d.reference}">
                    ${d.label} – ${d.short_edge} × ${d.long_edge} cm
                  </label>
                </span>
                `
            )
        ;

        /* Finishes */
        form
            .append('div')
            .attr('class', 'section-option-label')
            .text(_('Finish'))
        ;
        form
            .append('div')
            .attr('class', `choices ${PhotoOrder.FINISHES_CHOICES_CLS}`)
        ;

        /* Frames */
        form
            .append('div')
            .attr('class', 'section-option-label')
            .text(_('Frame'))
        ;
        form
            .append('div')
            .attr('class', `choices ${PhotoOrder.FRAMES_CHOICES_CLS}`)
        ;

        const priceWrapper = d3.select(this.wrapper)
            .append('div')
            .attr('class', 'total-price-wrapper')
        ;
        priceWrapper
            .append('span')
            .text(_("Price:"))
        ;
        priceWrapper
            .append('span')
            .attr('class', 'total')
            .text(_('[Please select options]'))
        ;

    }

    private onFormChange(event: Event) {
        const target = <HTMLInputElement>event.target;
        switch (target.name) {
            case 'format' :
                this.selectedOptions.format = target.value;
                this.updateFinishes();
                break;

            case 'finish' :
                this.selectedOptions.finish = target.value;
                this.updateFrames();
                break;
        }
    }

    private updateFinishes() {
        let finishes: Finish[] = [];
        for (let finish of this.printInfos.finishes) {
            for (let fmt_price of finish.formats_prices) {
                if (fmt_price.reference === this.selectedOptions.format)
                    finishes.push(finish);
            }
        }
        d3.select(this.wrapper).select(`.choices.${PhotoOrder.FINISHES_CHOICES_CLS}`)
            .html('')
            .selectAll('div')
            .data(finishes)
            .enter()
            .append('div')
            .html((d: Finish) => `
                <div>
                  <label>
                    <input type="radio" name="finish" value="${d.reference}">
                    ${d.label}
                  </label>
                  <div class="description">
                    ${d.description}
                  </div>
                </div>
            `);
    }

    private updateFrames() {
        let frames: Frame[] = [];
        const form = <HTMLFormElement>d3.select(this.wrapper).select('form').node();
        const fmtRef = (<RadioNodeList>form.elements.namedItem('format')).value;
        for (let frame of this.printInfos.frames) {
            if((new Set(frame.finishes)).has(this.selectedOptions.finish) &&
                (new Set(frame.formats_prices.map((e)=>e.reference))).has(fmtRef))
                frames.push(frame);
        }
        d3.select(this.wrapper).select(`.choices.${PhotoOrder.FRAMES_CHOICES_CLS}`)
            .html('')
            .selectAll('div')
            .data(frames)
            .enter()
            .append('div')
            .html((d: Finish) => `
                <div>
                  <label>
                    <input type="radio" name="frame" value="${d.reference}">
                    ${d.label}
                  </label>
                  <div class="description">
                    ${d.description}
                  </div>
                </div>
            `);

    }
}

function main() {
    const portal_url = document.body.getAttribute('data-portal_url');

    i18next
        .use(HttpApi)
        .use(LanguageDetector)
        .init({
            cleanCode: true,
            ns: ['photoprint',],
            defaultNS: 'photoprint',
            nsSeparator: false,
            keySeparator: false,
            backend: {
                loadPath: portal_url + '/photoprint/jsbuild/locales/{{lng}}/{{ns}}.json',
            },
            detection: {
                order: [
                    'navigator',
                    'querystring',
                    'cookie',
                    'localStorage',
                    'sessionStorage',
                    'navigator',
                    'htmlTag',
                    'path',
                    'subdomain'
                ],
            },
        })
        .then(() => {
            const uid = document.getElementById('pp-photo-infos')?.getAttribute('data-cmf_uid');
            const wrapper = document.getElementById('sale-options');
            new PhotoOrder(portal_url, uid, wrapper);
        });

}

window.addEventListener('load', () => main());