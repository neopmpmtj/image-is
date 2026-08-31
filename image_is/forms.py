from django import forms

from image_is.prompt_presets import (
    ComposeEvalTextError,
    compose_eval_text,
    default_preset_id,
    preset_choices,
)


class NewAnalysisForm(forms.Form):
    image = forms.ImageField(
        label="Upload one image",
        widget=forms.ClearableFileInput(
            attrs={"accept": "image/png,image/jpeg,image/webp,image/gif"}
        ),
    )
    description = forms.CharField(
        label="Session description",
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
        help_text="Optional. What this analysis is for — used to find it later.",
    )
    omit_instructions = forms.BooleanField(
        label="Omit system instructions",
        required=False,
        initial=False,
        help_text="Send only additional text as the user prompt (for short yes/no questions).",
    )
    prompt_preset = forms.ChoiceField(
        label="System instructions",
        choices=[],
        initial=default_preset_id,
        help_text="Sent as system/developer instructions when enabled.",
    )
    additional = forms.CharField(
        label="Additional instructions",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text="Appended to the preset when system instructions are on. Required when they are omitted.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["prompt_preset"].choices = preset_choices()

    def clean(self):
        cleaned = super().clean()
        if self.errors:
            return cleaned
        try:
            instructions, user_prompt = compose_eval_text(
                omit_instructions=cleaned.get("omit_instructions", False),
                preset_id=cleaned.get("prompt_preset", default_preset_id()),
                additional=cleaned.get("additional", ""),
            )
        except ComposeEvalTextError as exc:
            raise forms.ValidationError(str(exc)) from exc
        cleaned["instructions"] = instructions
        cleaned["user_prompt"] = user_prompt
        return cleaned
