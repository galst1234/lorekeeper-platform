/**
 * SuperTokens prebuilt UI ships its own light-only theme, driven entirely by
 * `--palette-*` custom properties scoped to `[data-supertokens~="container"]`
 * (see supertokens-auth-react's bundled default CSS). It has no awareness of
 * our `.dark` class, so without this override the auth widget stays white
 * regardless of the app's theme.
 *
 * Values below are the sRGB equivalents of this app's `.dark` design tokens
 * (see `--background`, `--foreground`, etc. in `src/index.css`), computed via
 * the OKLCH -> sRGB conversion so the widget matches the rest of the app.
 * A few elements (provider sign-in buttons, dividers) hardcode colors instead
 * of using the palette variables, so those are overridden directly.
 */
export const SUPERTOKENS_DARK_THEME_STYLE = `
  .dark [data-supertokens~="container"] {
    --palette-background: 10, 10, 10;
    --palette-inputBackground: 44, 44, 47;
    --palette-inputBorder: 36, 36, 39;
    --palette-primary: 65, 122, 255;
    --palette-primaryBorder: 65, 122, 255;
    --palette-success: 0, 162, 66;
    --palette-successBackground: 6, 41, 17;
    --palette-error: 250, 104, 93;
    --palette-errorBackground: 57, 20, 17;
    --palette-textTitle: 250, 250, 250;
    --palette-textLabel: 250, 250, 250;
    --palette-textInput: 250, 250, 250;
    --palette-textPrimary: 160, 160, 168;
    --palette-textLink: 65, 122, 255;
    --palette-buttonText: 10, 10, 10;
    --palette-textGray: 160, 160, 168;
    --palette-superTokensBrandingBackground: 44, 44, 47;
    --palette-superTokensBrandingText: 160, 160, 168;
    --palette-buttonGreyedOut: 44, 44, 47;

    border: 1px solid rgb(36, 36, 39);
  }

  .dark [data-supertokens~="divider"] {
    border-bottom-color: rgb(36, 36, 39);
  }

  .dark [data-supertokens~="buttonWithArrow"] {
    border-color: rgb(36, 36, 39);
  }

  .dark [data-supertokens~="button"][data-supertokens~="providerButton"] {
    background-color: rgb(10, 10, 10);
    border-color: rgb(36, 36, 39);
    color: rgb(250, 250, 250);
  }

  .dark [data-supertokens~="button"][data-supertokens~="providerButton"]:hover {
    background-color: rgb(44, 44, 47);
  }
`;
