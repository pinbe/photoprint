import * as d3 from "d3";

class PhotoOrder {
    private readonly uid: string;
    private readonly portal_url: string;

    constructor(portal_url: string,
                uid: string) {
        this.uid = uid;
        this.portal_url = portal_url;
        const params = new FormData();
        params.append('cmf_uid', this.uid)
        d3.json(
            `${this.portal_url}/portal_photo_print/getEffectivePrintingOptionsFor`,
            {
                method: 'POST',
                body: params
            })
            .then((value => console.log(value)))
        ;
    }
}

function main() {
    const uid = document.getElementById('pp-photo-infos')?.getAttribute('data-cmf_uid');
    new PhotoOrder(document.body.getAttribute('data-portal_url'), uid);
}

window.addEventListener('load', () => main());