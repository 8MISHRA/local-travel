# Models package
# All models are imported here for Alembic auto-detection.
from app.models.base import AuditMixin  # noqa: F401
from app.models.user import (  # noqa: F401
    User,
    UserRole,
    RefreshToken,
)
from app.models.destination import (  # noqa: F401
    Destination,
    SubDestination,
    SubDestinationCategory,
)
from app.models.package import (  # noqa: F401
    Package,
    PricingTier,
    Itinerary,
    TravellerType,
)
from app.models.booking import (  # noqa: F401
    Booking,
    BookingStatus,
    BookingStatusHistory,
    BookingScout,
    BookingDriver,
)
from app.models.payment import (  # noqa: F401
    Payment,
    PaymentStatus,
    Refund,
    RefundStatus,
)
from app.models.invoice import Invoice  # noqa: F401
from app.models.review import (  # noqa: F401
    Review,
    ReviewEntityType,
    ReviewStatus,
)
from app.models.gallery import (  # noqa: F401
    GalleryImage,
    GalleryEntityType,
)
from app.models.blog import (  # noqa: F401
    BlogPost,
    BlogPostStatus,
)
from app.models.scout import (  # noqa: F401
    Scout,
    ScoutAvailability,
    OperatingArea,
)
from app.models.driver import (  # noqa: F401
    Driver,
    DriverAvailability,
)
from app.models.hotel import (  # noqa: F401
    Hotel,
    RoomType,
    RoomAvailability,
)
from app.models.enterprise import (  # noqa: F401
    EnterpriseBooking,
    EnterpriseBookingStatus,
)
from app.models.coupon import (  # noqa: F401
    Coupon,
    DiscountType,
)
from app.models.wishlist import Wishlist  # noqa: F401
from app.models.notification import (  # noqa: F401
    Notification,
    DeliveryChannel,
)
from app.models.support import (  # noqa: F401
    SupportTicket,
    TicketReply,
    TicketPriority,
    TicketStatus,
)
from app.models.audit_log import AuditLog  # noqa: F401
