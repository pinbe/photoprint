import * as d3 from "d3";
import i18next, {TOptions} from "i18next";
import HttpApi from 'i18next-http-backend';
import LanguageDetector from 'i18next-browser-languagedetector'

const _ = (s: string, options?:TOptions): string => i18next.t(s, options);

type Sel = d3.Selection<HTMLElement, any, HTMLElement, any>;
type I18NString = {[lang: string] : string};
type PriceRange = {
    from: number
    to: number,
    price: number
};
type Format = {
    reference: string,
    label: I18NString,
    short_edge: number,
    long_edge: number,
    copies: number,
    prices_ranges: Array<PriceRange>,
    finishes: Array<string>,
};

type PrintInfos = {
    formats: Array<Format>
};

class PrintOptionsEditor {
    private absUrl: string;
    private formatsWrapper: HTMLTableDataCellElement;

    constructor(absUrl:string) {
        this.absUrl = absUrl;
        let cells = document.querySelectorAll<HTMLTableDataCellElement>('#print_options_editor > tr > td');
        this.formatsWrapper = cells[0];

        d3.json(`${this.absUrl}/printingOptions/printoffer/json`)
            .then((infos: PrintInfos) => {
                this.initFormats(infos.formats);
            })
    }

    private initFormats(formats: Array<Format>) {
        d3.select(this.formatsWrapper)
            // .append('div')
            .selectAll('div')
            .data(formats)
            .enter()
            .append('div')
            .html((d, i, g) => {
                console.log(d, i, g);
                let lbl= '';
                for (let [lang, value] of Object.entries(d.label)) {
                    lbl += `<li><span>${value}</span>@<span>${lang}</span></li>`
                }
                return `
                <table class="TwoColumnForm">
                  <tr>
                    <td colspan="2" style="text-align: right">
                      <a href="#" title="${_("Edit")}">
                        <i class="fas fa-edit"></i>
                      </a>
                      <a href="#" title="${_("Delete")}">
                        <i class="fas fa-backspace"></i>
                      </a>
                    </td>
                  </tr>
                  <tr>
                    <th>${_("Reference")}</th>
                    <td data-name="reference">${d.reference}</td>
                  </tr>
                  <tr>
                    <th>${_("Label")}</th>
                    <td>
                      <ul style="list-style: none">${lbl}</ul>
                    </td>
                  </tr>
                  <tr>
                    <th>${_("Short edge")}</th>
                    <td>
                      <span data-name="short_edge">${d.short_edge}</span> cm
                    </td>
                  </tr>
                  <tr>
                    <th>${_("Long edge")}</th>
                    <td>
                      <span data-name="long_edge">${d.long_edge}</span> cm
                    </td>
                  </tr>
                  <tr>
                    <th>${_("Copies")}</th>
                    <td>
                      <span data-name="copies">${d.copies}</span>
                    </td>
                  </tr>
                </table>
                `
                }
            )
        ;
        d3.select(this.formatsWrapper)
            .append('div')
            .style('text-align', 'center')
            .append('a')
            .on('click', () => this.createFormat())
            .attr('href', '#')
            .attr('title', _("Add new format…"))
            .append('i')
            .attr('class', 'fas fa-plus')
        ;
    }

    private createFormat() {
        d3.event.stopPropagation();
        d3.event.preventDefault();
        console.log('Ajouter !');
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
            backend: {
                loadPath: portal_url+'/photoprint/jsbuild/locales/{{lng}}/{{ns}}.json',
            },
            detection: {
                order: ['navigator',
                    'querystring',
                    'cookie',
                    'localStorage',
                    'sessionStorage',
                    'navigator',
                    'htmlTag',
                    'path',
                    'subdomain'],
            },
        })
        .then(
            () => new PrintOptionsEditor(document.body.getAttribute('data-absolute_url')));
}

window.addEventListener('load', ()=>main());