import {WidgetBasedFormManager} from "./components/WidgetBasedFormManager";

function main() {
    new WidgetBasedFormManager('#print_order_templates_editing_area');
}

window.addEventListener('load', ()=>main());