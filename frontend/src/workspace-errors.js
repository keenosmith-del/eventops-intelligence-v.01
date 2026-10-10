export function workspaceError(error) {
  if (error.message.includes("PostgreSQL"))
    return "This request could not be completed. Please try again.";
  if (error.message.includes("Cannot reach"))
    return "Connection unavailable. Please try again.";
  return error.message;
}
