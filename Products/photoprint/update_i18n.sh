#! /bin/sh

if [ !$1 ]; then
    ZCML=$INSTANCE_HOME/etc/site.zcml
else
    ZCML=$1
fi

i18nextract --path . --site_zcml $ZCML --domain photoprint -o locales

cat locales/photoprint.pot locales/photoprint-manual.pot > locales/photoprint-all.pot
mv locales/photoprint-all.pot locales/photoprint.pot

msgmerge --update --no-fuzzy-matching locales/fr/LC_MESSAGES/photoprint.po locales/photoprint.pot
msgmerge --update --no-fuzzy-matching locales/en/LC_MESSAGES/photoprint.po locales/photoprint.pot
