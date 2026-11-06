// Prints the window number of the frontmost normal window owned by an app
// whose name contains the given text. Exits 1 if none found.
import CoreGraphics
import Foundation

let name = CommandLine.arguments.dropFirst().first ?? ""
let opts: CGWindowListOption = [.optionOnScreenOnly, .excludeDesktopElements]
guard let list = CGWindowListCopyWindowInfo(opts, kCGNullWindowID) as? [[String: Any]] else { exit(1) }

for w in list {
    let owner = w[kCGWindowOwnerName as String] as? String ?? ""
    let bounds = w[kCGWindowBounds as String] as? [String: Any] ?? [:]
    let width = bounds["Width"] as? Double ?? 0
    if owner.localizedCaseInsensitiveContains(name), width > 50,
       let id = w[kCGWindowNumber as String] as? Int {
        print(id)
        exit(0)
    }
}
exit(1)
