// This function takes an error object and returns a user-friendly error message based on the
// error's content. It checks for specific error messages related to PostgreSQL and connection
// issues, providing a more understandable message for the user. If the error does not match any
// known patterns, it returns the original error message.
export function workspaceError(error) {
  if (error.message.includes("PostgreSQL"))
    return "This request could not be completed. Please try again.";

  if (error.message.includes("Cannot reach"))
    return "Connection unavailable. Please try again.";

  return error.message;
}
