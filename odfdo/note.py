# Copyright 2018 Jérôme Dumonteil
# Copyright (c) 2009-2010 Ars Aperta, Itaapy, Pierlis, Talend.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Authors (odfdo project): jerome.dumonteil@gmail.com
# The odfdo project is a derivative work of the lpod-python project:
# https://github.com/lpod/lpod-python
# Authors: Hervé Cauwelier <herve@itaapy.com>
#          Romain Gauthier <romain@itaapy.com>
#          Jerome Dumonteil <jerome.dumonteil@itaapy.com>

from datetime import datetime
from types import FunctionType

from .element import Element, register_element_class
from .utils import to_str


def get_unique_office_name(element=None):
    """Provide an autogenerated unique <office:name> for the document.
    """
    if element is not None:
        body = element.document_body
    else:
        body = None
    if body:
        used = body.get_office_names()
    else:
        used = []
    # unplugged current paragraph:
    if element is not None:
        used.extend(element.get_office_names())
    i = 1
    while True:
        name = '__Fieldmark__lpod_%s' % i
        if name in used:
            i += 1
            continue
        break
    return name


class Note(Element):
    """Either a footnote or a endnote element with the given text,
    optionally referencing it using the given note_id.

    Arguments:

        note_class -- 'footnote' or 'endnote'

        note_id -- str

        citation -- str

        body -- str or Element

    Return: Note
    """
    _tag = 'text:note'
    _properties = (('note_class', 'text:note-class'), ('note_id', 'text:id'))

    def __init__(self,
                 note_class='footnote',
                 note_id=None,
                 citation=None,
                 body=None,
                 **kwargs):
        super().__init__(**kwargs)
        if self._do_init:
            self.insert(Element.from_tag('text:note-body'), position=0)
            self.insert(Element.from_tag('text:note-citation'), position=0)
            self.note_class = note_class
            if note_id is not None:
                self.note_id = note_id
            if citation is not None:
                self.citation = citation
            if body is not None:
                self.note_body = body

    @property
    def citation(self):
        note_citation = self.get_element('text:note-citation')
        return note_citation.text

    @citation.setter
    def citation(self, text):
        note_citation = self.get_element('text:note-citation')
        note_citation.text = text

    @property
    def note_body(self):
        note_body = self.get_element('text:note-body')
        return note_body.text_content

    @note_body.setter
    def note_body(self, text_or_element):
        note_body = self.get_element('text:note-body')
        if isinstance(text_or_element, (str, bytes)):
            note_body.text_content = text_or_element
        elif isinstance(text_or_element, Element):
            note_body.clear()
            note_body.append(text_or_element)
        else:
            raise ValueError(
                'Unexpected type for body: "%s"' % type(text_or_element))

    def check_validity(self):
        if not self.note_class:
            raise ValueError('note class must be "footnote" or "endnote"')
        if not self.note_id:
            raise ValueError("notes must have an id")
        if not self.citation:
            raise ValueError("notes must have a citation")
        if not self.note_body:
            pass


Note._define_attribut_property()


class Annotation(Element):
    """Annotation element credited to the given creator with the
    given text, optionally dated (current date by default).
    If name not provided and some parent is provided, the name is autogenerated.

    Arguments:

        text -- str or odf_element

        creator -- str

        date -- datetime

        name -- str

        parent -- Element

    Return: Annotation
    """
    _tag = 'office:annotation'
    _properties = (('name', 'office:name'), ('note_id', 'text:id'))

    def __init__(self,
                 text_or_element=None,
                 creator=None,
                 date=None,
                 name=None,
                 parent=None,
                 **kwargs):
        # fixme : use offset
        # TODO allow paragraph and text styles
        super().__init__(**kwargs)

        if self._do_init:
            self.note_body = text_or_element
            if creator:
                self.dc_creator = creator
            if date is None:
                date = datetime.now()
            self.dc_date = date
            if not name:
                name = get_unique_office_name(parent)
                self.name = name

    @property
    def note_body(self):
        return self.text_content

    @note_body.setter
    def note_body(self, text_or_element):
        if isinstance(text_or_element, (str, bytes)):
            self.text_content = text_or_element
        elif isinstance(text_or_element, Element):
            self.clear()
            self.append(text_or_element)
        else:
            raise TypeError('expected unicode or Element')

    @property
    def start(self):
        """Return self.
        """
        return self

    @property
    def end(self):
        """Return the corresponding annotation-end tag or None.
        """
        name = self.name
        parent = self.parent
        if parent is None:
            raise ValueError("Can not find end tag: no parent available.")
        body = self.document_body
        if not body:
            body = parent
        return body.get_annotation_end(name=name)

    def get_annotated(self, as_text=False, no_header=True, clean=True):
        """Returns the annotated content from an annotation.

        If no content exists (single position annotation or annotation-end not
        found), returns [] (or u'' if text flag is True).
        If as_text is True: returns the text content.
        If clean is True: suppress unwanted tags (deletions marks, ...)
        If no_header is True: existing text:h are changed in text:p
        By default: returns a list of odf_element, cleaned and without headers.

        Arguments:

            as_text -- boolean

            clean -- boolean

            no_header -- boolean

        Return: list or Element or text
        """
        end = self.end
        if end is None:
            if as_text:
                return ''
            return None
        body = self.document_body
        if not body:
            body = self.root
        return body.get_between(
            self, end, as_text=as_text, no_header=no_header, clean=clean)

    def delete(self, child=None):
        """Delete the given element from the XML tree. If no element is given,
        "self" is deleted. The XML library may allow to continue to use an
        element now "orphan" as long as you have a reference to it.

        For Annotation : delete the annotation-end tag if exists.

        Arguments:

            child -- Element
        """
        if child is not None:  # act like normal delete
            return super(Annotation, self).delete(child)
        end = self.end
        if end:
            end.delete()
        # act like normal delete
        return super(Annotation, self).delete()

    def check_validity(self):
        if not self.note_body:
            raise ValueError("annotation must have a body")
        if not self.dc_creator:
            raise ValueError("annotation must have a creator")
        if not self.dc_date:
            self.dc_date = datetime.now()


Annotation._define_attribut_property()


class AnnotationEnd(Element):
    """AnnotationEnd: the <office:annotation-end> element may be used to
    define the end of a text range of document content that spans element
    boundaries. In that case, an <office:annotation> element shall precede
    the <office:annotation-end> element. Both elements shall have the same
    value for their office:name attribute. The <office:annotation-end> element
    shall be preceded by an <office:annotation> element that has the same
    value for its office:name attribute as the <office:annotation-end>
    element. An <office:annotation-end> element without a preceding
    <office:annotation> element that has the same name assigned is ignored.
    """
    _tag = 'office:annotation-end'
    _properties = (('name', 'office:name'), )

    def __init__(self, annotation=None, name=None, **kwargs):
        """Initialize an AnnotationEnd element. Either annotation or name must be
        provided to have proper reference for the annotation-end.

        Arguments:

            annotation -- odf_annotation element

            name -- str

        Return: AnnotationEnd
        """
        # fixme : use offset
        # TODO allow paragraph and text styles
        super().__init__(**kwargs)
        if self._do_init:
            if annotation:
                name = annotation.name
            if not name:
                raise ValueError("Annotation-end must have a name")
            self.name = name

    @property
    def start(self):
        """Return the corresponding annotation starting tag or None.
        """
        name = self.name
        parent = self.parent
        if parent is None:
            raise ValueError("Can not find start tag: no parent available.")
        body = self.document_body
        if not body:
            body = parent
        return body.get_annotation(name=name)

    @property
    def end(self):
        """Return self.
        """
        return self


AnnotationEnd._define_attribut_property()

register_element_class(Note)
register_element_class(Annotation)
register_element_class(AnnotationEnd)
