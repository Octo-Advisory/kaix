import React from "react";
import {
  PanelRightOpen,
  PanelRightClose,
  SquarePen,
  ChevronRight,
  ChevronLeft,
  Settings,
  LogOut,
  Send,
  Copy,
  Factory,
  MapPinned,
  MapPin,
  ClipboardCheck,
  CalendarClock,
  Plus,
  Trash,
  Save,
  History
} from "lucide-react";
import { IoSearch, IoAlertCircleOutline } from "react-icons/io5";
import { FaHandHoldingUsd, FaRegLightbulb } from "react-icons/fa";
import { LuUserRoundCheck } from "react-icons/lu";
import { IoIosClose } from "react-icons/io";
import { HiOutlineDocumentReport } from "react-icons/hi";
import { FaUserLarge, FaArrowLeft, FaArrowRight, FaListCheck,FaLandmark, FaUserGroup, FaUser } from "react-icons/fa6";
import { BsBuildingCheck, BsShop  } from "react-icons/bs";
import { TbTriangleInvertedFilled, TbTriangleFilled } from "react-icons/tb";
import { HiOutlineClipboardDocumentCheck, HiOutlineClipboardDocumentList,HiOutlineQuestionMarkCircle } from "react-icons/hi2";
import { GoInfo } from "react-icons/go";
import { HiOutlineCurrencyDollar } from "react-icons/hi2";
import FinancialSummary from './IconPNGs/financial-planning (1).png'
import IncentiveTitle from './IconPNGs/incentive.png'
import IncentiveName from './IconPNGs/agreement.png'
import ApprovalName from './IconPNGs/approve.png'
import ApprovalTitle from './IconPNGs/attestation.png'
import { AiOutlineClear, AiOutlineDollar } from "react-icons/ai";
import { RiBuilding2Line } from "react-icons/ri";
import { FiSend } from "react-icons/fi";

const DEFAULT_SIZE = 24;
const DEFAULT_STROKE = 1;

// Helper HOC to apply default props
const withDefaults = (IconComponent) => (props) =>
  React.createElement(IconComponent, {
    size: DEFAULT_SIZE,
    strokeWidth: DEFAULT_STROKE,
    ...props
  });

const PNGIcon = ({ src, alt = "icon", size = DEFAULT_SIZE, className = "", ...props }) => {
  return React.createElement("img", {
    src,
    alt,
    width: size,
    height: size,
    className: `inline-block object-contain ${className}`,
    style: { display: "inline-block", objectFit: "contain" },
    ...props,
  });
};


export const FinancialSummaryIcon = (props) =>
  React.createElement(PNGIcon, {
    src: FinancialSummary,
    alt: "Incentive",
    ...props
  });

export const IncentiveTitleIcon = (props) =>
  React.createElement(PNGIcon, {
    src: IncentiveTitle,
    alt: "Incentive Title",
    ...props
  });
export const IncentiveNameIcon = (props) =>
  React.createElement(PNGIcon, {
    src: IncentiveName,
    alt: "Incentive Name",
    ...props
  });

export const ApprovalTitleIcon = (props) =>
  React.createElement(PNGIcon, {
    src: ApprovalTitle,
    alt: "Approval Title",
    ...props
  });
export const ApprovalNameIcon = (props) =>
  React.createElement(PNGIcon, {
    src: ApprovalName,
    alt: "Approval Name",
    ...props
  });


  
  
  // Wrapped React/Lucide Icons
export const IncentiveIcon = withDefaults(FaHandHoldingUsd)
export const SideBarOpenIcon = withDefaults(PanelRightClose);
export const SideBarCloseIcon = withDefaults(PanelRightOpen);
export const SearchIcon = withDefaults(IoSearch);
export const EditIcon = withDefaults(SquarePen);
export const BulbIcon = withDefaults(FaRegLightbulb);
export const ReportIcon = withDefaults(HiOutlineDocumentReport);
export const ChevronRightIcon = withDefaults(ChevronRight);
export const ChevronLeftIcon = withDefaults(ChevronLeft);
export const SettingsIcon = withDefaults(Settings);
export const UserIcon = withDefaults(FaUserLarge);
export const LogoutIcon = withDefaults(LogOut);
export const QuestionMarkIcon = withDefaults(HiOutlineQuestionMarkCircle);
export const SendIcon = withDefaults(Send);
export const CopyTextIcon = withDefaults(Copy);
export const BuildingIcon = withDefaults(FaLandmark);
export const EligibilityIcon = withDefaults(LuUserRoundCheck)
export const FactoryIcon = withDefaults(Factory);
export const MapPinnedIcon = withDefaults(MapPinned);
export const MapPinIcon = withDefaults(MapPin);
export const ArrowLeftIcon = withDefaults(FaArrowLeft);
export const ArrowRightIcon = withDefaults(FaArrowRight);
export const DollarIcon = withDefaults(HiOutlineCurrencyDollar)
export const ScheduleIcon = withDefaults(CalendarClock);
export const ClipboardCheckIcon = withDefaults(ClipboardCheck);
export const AdditionalDetailIcon = withDefaults(HiOutlineClipboardDocumentList);
export const ListCheckIcon = withDefaults(FaListCheck);
export const InfoIcon = withDefaults(GoInfo);
export const TriangleDownIcon = withDefaults(TbTriangleInvertedFilled);
export const TriangleUpIcon = withDefaults(TbTriangleFilled);
export const AlertIcon = withDefaults(IoAlertCircleOutline);
export const CloseIcon = withDefaults(IoIosClose);
export const AddIcon = withDefaults(Plus);
export const DeleteIcon = withDefaults(Trash);
export const SaveIcon = withDefaults(Save);
export const HistoryIcon = withDefaults(History)
export const ShopIcon = withDefaults(BsShop)
export const UserGroupIcon = withDefaults(FaUserGroup)
export const BuildingLineIcon = withDefaults(RiBuilding2Line)
export const ClearIcon = withDefaults(AiOutlineClear)





