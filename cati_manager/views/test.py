from __future__ import absolute_import

from pyramid.view import view_config

from pyramid.httpexceptions import HTTPFound

import colander
import deform


class ExampleSchema(deform.schema.CSRFSchema):

    name = colander.SchemaNode(
        colander.String(),
        title="Name")

    age = colander.SchemaNode(
        colander.Int(),
        default=18,
        title="Age",
        description="Your age in years")


@view_config(route_name='test', renderer='templates/layout.jinja2', permission='test_project_credential')
def test(request):
    """Sample Deform form with validation."""

    schema = ExampleSchema().bind(request=request)

    # Create a styled button with some extra Bootstrap 3 CSS classes
    process_btn = deform.form.Button(name='process', title="Process")
    form = deform.form.Form(schema, buttons=(process_btn,))

    # User submitted this form
    if request.method == "POST":
        if 'process' in request.POST:

            try:
                appstruct = form.validate(request.POST.items())

                # Save form data from appstruct
                print("Your name:", appstruct["name"])
                print("Your age:", appstruct["age"])

                # Thank user and take him/her to the next page
                request.session.flash('Thank you for the submission.', 'success', False)
                request.session.flash('<strong>Error !</strong> But it is useless now.', 'danger', False)

                # Redirect to the page shows after succesful form submission
                return HTTPFound("/test")

            except deform.exception.ValidationFailure as e:
                # Render a form version where errors are visible next to the fields,
                # and the submitted values are posted back
                rendered_form = e.render()
    else:
        # Render a form with initial default values
        rendered_form = form.render()

    return {
        # This is just rendered HTML in a string
        # and can be embedded in any template language
        "content": rendered_form + '''<table>
<tr><td><div contenteditable>I'm editable</div></td><td><div contenteditable>I'm also editable</div></td></tr>
<tr><td>I'm not editable</td></tr>
</table>''',
    }

